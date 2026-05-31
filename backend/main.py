"""
main.py — FastAPI application entry point for the GitHub Repository Suggester.

Endpoints:
    POST /suggest   — Returns ranked GitHub repo suggestions for a project description
    GET  /health    — Health check

Core flow for POST /suggest:
    1. Validate request (Pydantic)
    2. Generate BERT embedding of the description (sentence-transformers)
    3. Semantic search via FAISS index
    4. Keyword + metadata search via Elasticsearch (graceful degrade if unavailable)
    5. Merge & deduplicate results
    6. Enrich top-10 with live GitHub API data (stars, last commit)
    7. Re-rank: semantic 40% + stars 20% + recency 20% + ES score 20%
    8. Return top-N results with explanations
"""
from __future__ import annotations

import logging
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from embedder import embed_text
from github_client import enrich_repos
from models import HealthResponse, SuggestRequest, SuggestResponse, RepoSuggestion
from ranker import merge_and_rank
from searcher import es_search, faiss_search

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="GitHub Repository Suggester API",
    description=(
        "Submit a natural language project description and get ranked GitHub "
        "repository suggestions powered by BERT embeddings, FAISS, and Elasticsearch."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow the Vite frontend (localhost:8080) and common dev ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "*",  # Remove in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["Utility"])
async def health_check():
    """Simple liveness probe."""
    return {"status": "ok"}


@app.post("/suggest", response_model=SuggestResponse, tags=["Suggest"])
async def suggest(request: SuggestRequest):
    """
    Analyse a natural language project description and return
    ranked GitHub repository suggestions.
    """
    description = request.description.strip()
    language = request.language.strip() if request.language else None
    limit = request.limit

    logger.info(
        "Suggest request — description=%r language=%r limit=%d",
        description[:80],
        language,
        limit,
    )

    # ------------------------------------------------------------------
    # Step 1: Generate BERT embedding
    # ------------------------------------------------------------------
    try:
        query_vec = embed_text(description)
    except Exception as exc:
        logger.error("Embedding failed: %s", exc)
        raise HTTPException(status_code=503, detail="Embedding service unavailable.")

    # ------------------------------------------------------------------
    # Step 2: FAISS semantic search
    # ------------------------------------------------------------------
    faiss_results = faiss_search(
        query_embedding=query_vec,
        top_k=20,
        language_filter=language,
    )
    logger.info("FAISS returned %d results.", len(faiss_results))

    # ------------------------------------------------------------------
    # Step 3: Elasticsearch keyword search
    # ------------------------------------------------------------------
    es_results = es_search(
        description=description,
        top_k=20,
        language_filter=language,
    )
    logger.info("ES returned %d results.", len(es_results))

    # ------------------------------------------------------------------
    # Step 4: If both backends returned nothing, raise a helpful error
    # ------------------------------------------------------------------
    if not faiss_results and not es_results:
        raise HTTPException(
            status_code=404,
            detail=(
                "No repositories found. Make sure the FAISS index is built "
                "by running `python indexer.py` first."
            ),
        )

    # ------------------------------------------------------------------
    # Step 5: Merge, deduplicate, preliminary rank
    # ------------------------------------------------------------------
    intent_summary, merged, follow_up = merge_and_rank(
        faiss_results=faiss_results,
        es_results=es_results,
        description=description,
        limit=max(limit, 10),   # keep top-10 for enrichment
    )

    # ------------------------------------------------------------------
    # Step 6: Enrich top-10 with live GitHub metadata
    # ------------------------------------------------------------------
    try:
        merged = await enrich_repos(merged)
        logger.info("GitHub enrichment complete.")
    except Exception as exc:
        logger.warning("GitHub enrichment failed (using cached data): %s", exc)

    # ------------------------------------------------------------------
    # Step 7: Final slice to requested limit + build response
    # ------------------------------------------------------------------
    # Re-sort after enrichment (stars may have changed)
    merged.sort(key=lambda x: x["relevance_score"], reverse=True)
    top_n = merged[:limit]

    # Re-assign ranks after final sort
    suggestions = [
        RepoSuggestion(
            rank=i + 1,
            repo=item["repo"],
            relevance_score=item["relevance_score"],
            why=item["why"],
            use_case_fit=item["use_case_fit"],
            stars=item.get("stars", 0),
            last_commit=item.get("last_commit", ""),
        )
        for i, item in enumerate(top_n)
    ]

    return SuggestResponse(
        intent_summary=intent_summary,
        suggestions=suggestions,
        follow_up_question=follow_up,
    )


# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info("Starting GitHub Suggester API on %s:%d …", host, port)
    uvicorn.run("main:app", host=host, port=port, reload=True)
