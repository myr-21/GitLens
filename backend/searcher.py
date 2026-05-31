"""
searcher.py — FAISS + Elasticsearch search logic.

Both search backends are optional and degrade gracefully:
  - If FAISS index doesn't exist → returns empty list
  - If Elasticsearch is unreachable → returns empty list
"""
from __future__ import annotations

import logging
import os
import pickle
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

INDEX_DIR = Path(__file__).parent / "faiss_index"
INDEX_FILE = INDEX_DIR / "repos.index"
META_FILE = INDEX_DIR / "repos_meta.pkl"

# ---------------------------------------------------------------------------
# FAISS — lazily loaded singletons
# ---------------------------------------------------------------------------
_faiss_index = None
_faiss_meta: list[dict] | None = None


def _load_faiss():
    global _faiss_index, _faiss_meta
    if _faiss_index is not None:
        return

    if not INDEX_FILE.exists() or not META_FILE.exists():
        logger.warning(
            "FAISS index not found at %s — run indexer.py first.", INDEX_DIR
        )
        return

    try:
        import faiss  # type: ignore

        _faiss_index = faiss.read_index(str(INDEX_FILE))
        with open(META_FILE, "rb") as f:
            _faiss_meta = pickle.load(f)
        logger.info("FAISS index loaded (%d vectors).", _faiss_index.ntotal)
    except Exception as exc:
        logger.error("Failed to load FAISS index: %s", exc)


def faiss_search(
    query_embedding: np.ndarray, top_k: int = 20, language_filter: str | None = None
) -> list[dict[str, Any]]:
    """
    Semantic vector search via FAISS.

    Returns a list of dicts with keys:
        repo, description, topics, language, stars, last_commit, faiss_score
    """
    _load_faiss()

    if _faiss_index is None or _faiss_meta is None:
        logger.warning("FAISS unavailable — returning empty results.")
        return []

    try:
        query = query_embedding.reshape(1, -1).astype(np.float32)
        distances, indices = _faiss_index.search(query, min(top_k * 3, _faiss_index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            meta = _faiss_meta[idx]

            # Language filter
            if language_filter and meta.get("language", "").lower() != language_filter.lower():
                continue

            results.append({**meta, "faiss_score": float(dist)})
            if len(results) >= top_k:
                break

        return results

    except Exception as exc:
        logger.error("FAISS search error: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Elasticsearch — optional keyword + metadata search
# ---------------------------------------------------------------------------
def _get_es_client():
    """Return an Elasticsearch client or None if unavailable."""
    try:
        from elasticsearch import Elasticsearch  # type: ignore

        es_url = os.getenv("ES_URL", "http://localhost:9200")
        es = Elasticsearch(es_url, request_timeout=3)
        if es.ping():
            return es
        logger.warning("Elasticsearch ping failed at %s.", es_url)
        return None
    except Exception as exc:
        logger.warning("Elasticsearch unavailable: %s", exc)
        return None


def es_search(
    description: str,
    top_k: int = 20,
    language_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Keyword + metadata search via Elasticsearch.

    Returns a list of dicts with keys:
        repo, description, topics, language, stars, last_commit, es_score
    """
    es = _get_es_client()
    if es is None:
        logger.warning("Elasticsearch unavailable — returning empty results.")
        return []

    try:
        must_clauses: list[dict] = [
            {
                "multi_match": {
                    "query": description,
                    "fields": ["description^3", "topics^2", "repo"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            }
        ]

        filter_clauses: list[dict] = []
        if language_filter:
            filter_clauses.append({"term": {"language": language_filter}})

        body: dict = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": must_clauses,
                    **({"filter": filter_clauses} if filter_clauses else {}),
                }
            },
        }

        response = es.search(index="repos", body=body)
        results = []
        for hit in response["hits"]["hits"]:
            src = hit["_source"]
            results.append({**src, "es_score": hit["_score"]})

        return results

    except Exception as exc:
        logger.error("Elasticsearch search error: %s", exc)
        return []
