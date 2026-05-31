"""
indexer.py — Seeds the FAISS index and Elasticsearch index with 30 example repos.

Run once before starting the server:
    python indexer.py

It will:
  1. Create a FAISS IndexFlatIP (inner product on L2-normalised vecs = cosine sim)
  2. Embed each seed repo's composite text
  3. Save the index to disk (faiss_index/repos.index)
  4. Persist the metadata store (faiss_index/repos_meta.pkl)
  5. Index all repos into Elasticsearch (graceful skip if ES is unreachable)
"""
from __future__ import annotations

import json
import logging
import os
import pickle
from pathlib import Path

import numpy as np

from embedder import embed_texts

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
INDEX_DIR = Path(__file__).parent / "faiss_index"
INDEX_FILE = INDEX_DIR / "repos.index"
META_FILE = INDEX_DIR / "repos_meta.pkl"

# ---------------------------------------------------------------------------
# Seed corpus — 30 diverse, well-known GitHub repos
# ---------------------------------------------------------------------------
SEED_REPOS = [
    {
        "repo": "facebook/react",
        "description": "A declarative, efficient, and flexible JavaScript library for building user interfaces and UI components.",
        "topics": ["javascript", "ui", "frontend", "component", "web"],
        "language": "JavaScript",
        "stars": 220000,
        "last_commit": "2024-12-01T00:00:00Z",
    },
    {
        "repo": "vuejs/vue",
        "description": "Progressive JavaScript framework for building reactive web interfaces with a gentle learning curve.",
        "topics": ["javascript", "vue", "frontend", "spa", "reactive"],
        "language": "JavaScript",
        "stars": 207000,
        "last_commit": "2024-11-15T00:00:00Z",
    },
    {
        "repo": "angular/angular",
        "description": "Platform for building mobile and desktop web applications with TypeScript and RxJS.",
        "topics": ["typescript", "angular", "frontend", "spa", "web"],
        "language": "TypeScript",
        "stars": 93000,
        "last_commit": "2024-12-05T00:00:00Z",
    },
    {
        "repo": "django/django",
        "description": "High-level Python web framework that encourages rapid development and clean, pragmatic design.",
        "topics": ["python", "web", "backend", "orm", "mvc"],
        "language": "Python",
        "stars": 80000,
        "last_commit": "2024-12-03T00:00:00Z",
    },
    {
        "repo": "tiangolo/fastapi",
        "description": "Modern, fast web framework for building APIs with Python based on standard type hints.",
        "topics": ["python", "api", "fastapi", "async", "rest"],
        "language": "Python",
        "stars": 76000,
        "last_commit": "2024-12-02T00:00:00Z",
    },
    {
        "repo": "expressjs/express",
        "description": "Fast, unopinionated, minimalist web framework for Node.js for building APIs and web apps.",
        "topics": ["nodejs", "javascript", "web", "api", "http"],
        "language": "JavaScript",
        "stars": 64000,
        "last_commit": "2024-11-20T00:00:00Z",
    },
    {
        "repo": "tensorflow/tensorflow",
        "description": "Open-source platform for machine learning and deep neural networks with Python and C++ support.",
        "topics": ["machine-learning", "deep-learning", "python", "neural-network", "ai"],
        "language": "Python",
        "stars": 185000,
        "last_commit": "2024-12-06T00:00:00Z",
    },
    {
        "repo": "pytorch/pytorch",
        "description": "Tensors and dynamic neural networks in Python with strong GPU acceleration for deep learning research.",
        "topics": ["machine-learning", "deep-learning", "python", "cuda", "tensor"],
        "language": "Python",
        "stars": 82000,
        "last_commit": "2024-12-07T00:00:00Z",
    },
    {
        "repo": "huggingface/transformers",
        "description": "State-of-the-art NLP with BERT, GPT, T5 and more. Pretrained models for text, vision, and audio.",
        "topics": ["nlp", "bert", "gpt", "transformers", "machine-learning", "python"],
        "language": "Python",
        "stars": 133000,
        "last_commit": "2024-12-08T00:00:00Z",
    },
    {
        "repo": "scikit-learn/scikit-learn",
        "description": "Machine learning in Python with simple, efficient tools for data mining and data analysis.",
        "topics": ["machine-learning", "python", "sklearn", "classification", "regression"],
        "language": "Python",
        "stars": 59000,
        "last_commit": "2024-11-28T00:00:00Z",
    },
    {
        "repo": "redis/redis",
        "description": "In-memory data structure store used as database, cache, message broker, and queue.",
        "topics": ["database", "cache", "nosql", "key-value", "pub-sub"],
        "language": "C",
        "stars": 67000,
        "last_commit": "2024-12-01T00:00:00Z",
    },
    {
        "repo": "mongodb/mongo",
        "description": "The MongoDB Database — document-oriented NoSQL database for modern applications.",
        "topics": ["database", "nosql", "mongodb", "document", "json"],
        "language": "C++",
        "stars": 26000,
        "last_commit": "2024-12-05T00:00:00Z",
    },
    {
        "repo": "postgres/postgres",
        "description": "The World's Most Advanced Open Source Relational Database with ACID compliance and extensibility.",
        "topics": ["database", "sql", "postgresql", "relational", "acid"],
        "language": "C",
        "stars": 16000,
        "last_commit": "2024-12-06T00:00:00Z",
    },
    {
        "repo": "docker/compose",
        "description": "Define and run multi-container Docker applications using a YAML configuration file.",
        "topics": ["docker", "containers", "devops", "orchestration", "yaml"],
        "language": "Python",
        "stars": 33000,
        "last_commit": "2024-11-25T00:00:00Z",
    },
    {
        "repo": "kubernetes/kubernetes",
        "description": "Container orchestration system for automating deployment, scaling, and management of containerized applications.",
        "topics": ["kubernetes", "containers", "devops", "orchestration", "cloud"],
        "language": "Go",
        "stars": 110000,
        "last_commit": "2024-12-08T00:00:00Z",
    },
    {
        "repo": "grafana/grafana",
        "description": "Open observability platform for monitoring and metrics dashboards, supporting Prometheus and many data sources.",
        "topics": ["monitoring", "dashboards", "metrics", "observability", "visualization"],
        "language": "TypeScript",
        "stars": 64000,
        "last_commit": "2024-12-07T00:00:00Z",
    },
    {
        "repo": "langchain-ai/langchain",
        "description": "Framework for building LLM-powered applications with chains, agents, and memory for AI workflows.",
        "topics": ["llm", "ai", "langchain", "python", "agents", "nlp"],
        "language": "Python",
        "stars": 92000,
        "last_commit": "2024-12-08T00:00:00Z",
    },
    {
        "repo": "openai/openai-python",
        "description": "Official Python library for the OpenAI API — GPT-4, DALL-E, Whisper, and Embeddings.",
        "topics": ["openai", "gpt", "ai", "python", "api", "llm"],
        "language": "Python",
        "stars": 22000,
        "last_commit": "2024-12-05T00:00:00Z",
    },
    {
        "repo": "apache/kafka",
        "description": "Distributed event streaming platform for high-performance data pipelines and real-time analytics.",
        "topics": ["kafka", "streaming", "messaging", "java", "distributed"],
        "language": "Java",
        "stars": 28000,
        "last_commit": "2024-12-04T00:00:00Z",
    },
    {
        "repo": "elastic/elasticsearch",
        "description": "Distributed, RESTful search and analytics engine capable of full-text search and structured queries.",
        "topics": ["search", "elasticsearch", "java", "full-text", "analytics"],
        "language": "Java",
        "stars": 70000,
        "last_commit": "2024-12-06T00:00:00Z",
    },
    {
        "repo": "nestjs/nest",
        "description": "Progressive Node.js framework for building efficient, scalable server-side applications with TypeScript.",
        "topics": ["typescript", "nodejs", "backend", "framework", "api"],
        "language": "TypeScript",
        "stars": 67000,
        "last_commit": "2024-12-03T00:00:00Z",
    },
    {
        "repo": "vercel/next.js",
        "description": "The React Framework for Production — SSR, SSG, API routes, and full-stack capabilities.",
        "topics": ["react", "nextjs", "fullstack", "ssr", "typescript"],
        "language": "JavaScript",
        "stars": 127000,
        "last_commit": "2024-12-08T00:00:00Z",
    },
    {
        "repo": "vitejs/vite",
        "description": "Next generation frontend build tool with lightning-fast HMR, ESM, and Rollup bundler.",
        "topics": ["vite", "build-tool", "frontend", "javascript", "esm"],
        "language": "TypeScript",
        "stars": 68000,
        "last_commit": "2024-12-07T00:00:00Z",
    },
    {
        "repo": "supabase/supabase",
        "description": "Open source Firebase alternative with Postgres, Auth, Storage, Realtime, and Edge Functions.",
        "topics": ["postgres", "firebase", "backend", "realtime", "auth"],
        "language": "TypeScript",
        "stars": 73000,
        "last_commit": "2024-12-08T00:00:00Z",
    },
    {
        "repo": "prisma/prisma",
        "description": "Next-generation ORM for Node.js and TypeScript with type-safe database queries and migrations.",
        "topics": ["orm", "typescript", "database", "nodejs", "postgresql"],
        "language": "TypeScript",
        "stars": 39000,
        "last_commit": "2024-12-05T00:00:00Z",
    },
    {
        "repo": "trpc/trpc",
        "description": "End-to-end typesafe APIs with TypeScript — no code generation, no REST, just pure type safety.",
        "topics": ["typescript", "api", "rpc", "fullstack", "react"],
        "language": "TypeScript",
        "stars": 35000,
        "last_commit": "2024-11-30T00:00:00Z",
    },
    {
        "repo": "celery/celery",
        "description": "Distributed task queue for Python applications supporting RabbitMQ, Redis, and many brokers.",
        "topics": ["python", "task-queue", "async", "celery", "redis"],
        "language": "Python",
        "stars": 24000,
        "last_commit": "2024-11-28T00:00:00Z",
    },
    {
        "repo": "pydantic/pydantic",
        "description": "Data validation and settings management using Python type annotations with runtime type checking.",
        "topics": ["python", "validation", "pydantic", "typing", "data"],
        "language": "Python",
        "stars": 21000,
        "last_commit": "2024-12-06T00:00:00Z",
    },
    {
        "repo": "sqlalchemy/sqlalchemy",
        "description": "Python SQL toolkit and Object Relational Mapper giving developers full power of SQL.",
        "topics": ["python", "sql", "orm", "database", "postgresql"],
        "language": "Python",
        "stars": 9500,
        "last_commit": "2024-12-04T00:00:00Z",
    },
    {
        "repo": "encode/httpx",
        "description": "Next generation HTTP client for Python with async support, HTTP/2, and type annotations.",
        "topics": ["python", "http", "async", "http2", "requests"],
        "language": "Python",
        "stars": 13000,
        "last_commit": "2024-11-22T00:00:00Z",
    },
]


# ---------------------------------------------------------------------------
# FAISS helpers
# ---------------------------------------------------------------------------
def build_faiss_index(embeddings: np.ndarray):
    """Create a FAISS IndexFlatIP (cosine sim on normalised vectors)."""
    import faiss  # type: ignore

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner Product == cosine on L2-normed vecs
    index.add(embeddings)
    return index


# ---------------------------------------------------------------------------
# Elasticsearch helpers
# ---------------------------------------------------------------------------
def index_into_elasticsearch(repos: list[dict]) -> bool:
    """
    Bulk-index repos into Elasticsearch.  Returns True on success, False on failure.
    """
    try:
        from elasticsearch import Elasticsearch  # type: ignore
        from dotenv import load_dotenv

        load_dotenv()
        es_url = os.getenv("ES_URL", "http://localhost:9200")
        es = Elasticsearch(es_url, request_timeout=5)

        if not es.ping():
            logger.warning("Elasticsearch is not reachable at %s — skipping ES indexing.", es_url)
            return False

        # Create index with mapping if it doesn't exist
        if not es.indices.exists(index="repos"):
            es.indices.create(
                index="repos",
                body={
                    "mappings": {
                        "properties": {
                            "repo": {"type": "keyword"},
                            "description": {"type": "text"},
                            "topics": {"type": "keyword"},
                            "language": {"type": "keyword"},
                            "stars": {"type": "integer"},
                            "last_commit": {"type": "date"},
                        }
                    }
                },
            )

        actions = []
        for repo in repos:
            actions.append({"index": {"_index": "repos", "_id": repo["repo"]}})
            actions.append(
                {
                    "repo": repo["repo"],
                    "description": repo["description"],
                    "topics": repo["topics"],
                    "language": repo["language"],
                    "stars": repo["stars"],
                    "last_commit": repo["last_commit"],
                }
            )

        es.bulk(body=actions, refresh=True)
        logger.info("Indexed %d repos into Elasticsearch.", len(repos))
        return True

    except Exception as exc:
        logger.warning("Elasticsearch indexing failed (will degrade gracefully): %s", exc)
        return False


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main():
    logger.info("Building FAISS index with %d seed repos …", len(SEED_REPOS))
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Build composite text per repo
    texts = [
        f"{r['repo']} {r['description']} {' '.join(r['topics'])}"
        for r in SEED_REPOS
    ]

    # 2. Generate embeddings (batch)
    logger.info("Generating embeddings …")
    embeddings = embed_texts(texts)          # shape: (N, 384)
    logger.info("Embeddings shape: %s", embeddings.shape)

    # 3. Build + save FAISS index
    import faiss  # type: ignore

    index = build_faiss_index(embeddings)
    faiss.write_index(index, str(INDEX_FILE))
    logger.info("FAISS index saved → %s", INDEX_FILE)

    # 4. Save metadata
    meta = [
        {
            "repo": r["repo"],
            "description": r["description"],
            "topics": r["topics"],
            "language": r["language"],
            "stars": r["stars"],
            "last_commit": r["last_commit"],
        }
        for r in SEED_REPOS
    ]
    with open(META_FILE, "wb") as f:
        pickle.dump(meta, f)
    logger.info("Metadata saved → %s", META_FILE)

    # 5. Elasticsearch (optional)
    index_into_elasticsearch(SEED_REPOS)

    logger.info("Indexing complete ✓")


if __name__ == "__main__":
    main()
