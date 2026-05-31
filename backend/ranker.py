"""
ranker.py — Merges FAISS + ES results, deduplicates, and re-ranks.

Re-ranking formula:
    final_score = 0.40 * semantic_score   (FAISS cosine similarity, normalised)
                + 0.20 * stars_score      (log-normalised)
                + 0.20 * recency_score    (exponential decay)
                + 0.20 * es_score         (normalised ES relevance)

Also generates:
  - why: one-line human reason for the suggestion
  - use_case_fit: short description of fit
  - intent_summary: summary of what the user is building
  - follow_up_question: clarifying question when intent is ambiguous
"""
from __future__ import annotations

import logging
import math
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _recency_score(last_commit: str) -> float:
    """exp(-days / 365) decay — 1.0 today, ~0.37 one year ago."""
    if not last_commit:
        return 0.3
    try:
        ts = last_commit.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        days = max(0.0, (datetime.now(timezone.utc) - dt).days)
        return math.exp(-days / 365.0)
    except Exception:
        return 0.3


def _stars_score(stars: int) -> float:
    """log10(stars + 1) / log10(200_000) clamped to [0, 1]."""
    if not stars or stars < 0:
        return 0.0
    return min(1.0, math.log10(stars + 1) / math.log10(200_000))


def _normalise(values: list[float]) -> list[float]:
    """Min-max normalise a list of floats to [0, 1]."""
    if not values:
        return values
    lo, hi = min(values), max(values)
    if hi == lo:
        return [1.0] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _extract_keywords(description: str) -> list[str]:
    """Very simple keyword extractor — strips stop words."""
    stop = {
        "a", "an", "the", "i", "want", "to", "build", "create", "make",
        "for", "with", "and", "or", "is", "are", "of", "in", "that",
        "my", "me", "us", "we", "need", "using", "use", "can", "app",
        "application", "project",
    }
    words = re.findall(r"[a-zA-Z]+", description.lower())
    return [w for w in words if w not in stop and len(w) > 2]


def _generate_why(repo: str, description: str, kw: list[str], repo_data: dict) -> str:
    """Generate a brief human-readable rationale."""
    topics = repo_data.get("topics", [])
    matching = [t for t in topics if t.lower() in [k.lower() for k in kw]]
    if matching:
        return (
            f"Matches your need for {', '.join(matching[:3])} — "
            f"{repo_data.get('description', '')[:80]}."
        )
    return f"Semantically similar to your description: {repo_data.get('description', '')[:80]}."


def _generate_use_case_fit(repo_data: dict, description: str) -> str:
    lang = repo_data.get("language", "")
    topics = repo_data.get("topics", [])
    parts = []
    if lang:
        parts.append(f"Written in {lang}")
    if topics:
        parts.append(f"covers {', '.join(topics[:4])}")
    return (". ".join(parts) + ".") if parts else "Good general fit for your project."


def _intent_summary(description: str, kw: list[str]) -> str:
    key = ", ".join(kw[:5]) if kw else "your project"
    return f"You are looking to build something related to: {key}."


def _follow_up(description: str, kw: list[str]) -> str | None:
    """Return a clarifying question when the description is short / vague."""
    if len(description.split()) < 6 or len(kw) < 2:
        return "Could you tell me more about the core feature or target users of your project?"
    return None


# ---------------------------------------------------------------------------
# Main merge + rank function
# ---------------------------------------------------------------------------

def merge_and_rank(
    faiss_results: list[dict[str, Any]],
    es_results: list[dict[str, Any]],
    description: str,
    limit: int = 5,
) -> tuple[str, list[dict[str, Any]], str | None]:
    """
    Merge FAISS + ES results, deduplicate, re-rank, return top-N.

    Returns:
        (intent_summary, ranked_list, follow_up_question)
        where each item in ranked_list is a fully decorated repo dict.
    """
    kw = _extract_keywords(description)

    # 1. Build unified pool keyed by "owner/name"
    pool: dict[str, dict[str, Any]] = {}

    # Normalise FAISS scores in [0, 1]
    faiss_scores = [r.get("faiss_score", 0.0) for r in faiss_results]
    norm_faiss = _normalise(faiss_scores)
    for repo_data, norm_score in zip(faiss_results, norm_faiss):
        key = repo_data["repo"]
        pool[key] = {**repo_data, "_faiss": norm_score, "_es": 0.0}

    # Normalise ES scores in [0, 1]
    es_scores = [r.get("es_score", 0.0) for r in es_results]
    norm_es = _normalise(es_scores)
    for repo_data, norm_score in zip(es_results, norm_es):
        key = repo_data["repo"]
        if key in pool:
            pool[key]["_es"] = norm_score
        else:
            pool[key] = {**repo_data, "_faiss": 0.0, "_es": norm_score}

    if not pool:
        return _intent_summary(description, kw), [], _follow_up(description, kw)

    # 2. Compute final scores
    scored: list[tuple[float, dict]] = []
    for key, data in pool.items():
        sem = data.get("_faiss", 0.0)
        es = data.get("_es", 0.0)
        stars = _stars_score(data.get("stars", 0))
        recency = _recency_score(data.get("last_commit", ""))

        final = 0.40 * sem + 0.20 * stars + 0.20 * recency + 0.20 * es
        scored.append((final, data))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:limit]

    # 3. Build output list
    ranked: list[dict[str, Any]] = []
    for rank_idx, (score, data) in enumerate(top, start=1):
        why = _generate_why(data["repo"], description, kw, data)
        fit = _generate_use_case_fit(data, description)
        ranked.append(
            {
                "rank": rank_idx,
                "repo": data["repo"],
                "relevance_score": round(score, 4),
                "why": why,
                "use_case_fit": fit,
                "stars": data.get("stars", 0),
                "last_commit": data.get("last_commit", ""),
            }
        )

    intent = _intent_summary(description, kw)
    follow_up = _follow_up(description, kw)
    return intent, ranked, follow_up
