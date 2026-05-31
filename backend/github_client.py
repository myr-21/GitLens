"""
github_client.py — Async GitHub API calls using httpx.

Enriches top candidate repos with live metadata:
  - stargazers_count
  - pushed_at (last commit date)

All calls are async and honour the GITHUB_TOKEN env var.
Errors are caught silently; the raw data is returned as-is on failure.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
_BASE_URL = "https://api.github.com"
_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if GITHUB_TOKEN:
    _HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


async def fetch_repo_meta(
    client: httpx.AsyncClient, repo: str
) -> dict[str, Any]:
    """
    Fetch live metadata for a single repo ("owner/name").

    Returns a dict with 'stars' and 'last_commit' keys,
    or empty dict on failure.
    """
    url = f"{_BASE_URL}/repos/{repo}"
    try:
        resp = await client.get(url, headers=_HEADERS, timeout=8.0)
        if resp.status_code == 404:
            logger.debug("Repo not found on GitHub: %s", repo)
            return {}
        resp.raise_for_status()
        data = resp.json()
        return {
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "last_commit": data.get("pushed_at", ""),
        }
    except httpx.HTTPStatusError as exc:
        logger.warning("GitHub API HTTP error for %s: %s", repo, exc.response.status_code)
        return {}
    except Exception as exc:
        logger.warning("GitHub API error for %s: %s", repo, exc)
        return {}


async def enrich_repos(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Concurrently enrich up to 10 repos with live GitHub metadata.

    Mutates each dict in-place (adds/updates 'stars' and 'last_commit').
    Returns the enriched list.
    """
    import asyncio

    top = repos[:10]
    async with httpx.AsyncClient() as client:
        tasks = [fetch_repo_meta(client, r["repo"]) for r in top]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for repo_dict, result in zip(top, results):
        if isinstance(result, dict) and result:
            repo_dict["stars"] = result.get("stars", repo_dict.get("stars", 0))
            repo_dict["last_commit"] = result.get("last_commit", repo_dict.get("last_commit", ""))

    return repos
