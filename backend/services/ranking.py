import math
from datetime import datetime, timezone
from typing import List, Dict, Any

def compute_recency_score(updated_at_str: str) -> float:
    """
    Compute recency score using exponential decay: exp(-days_since_update / 365.0)
    Updated today = 1.0
    Updated 1 year ago = 0.368
    Updated 2 years ago = 0.135
    """
    if not updated_at_str:
        return 0.0
        
    try:
        # Standardize ISO timestamp parsing
        # Remove trailing 'Z' if present, replace with offset
        ts_str = updated_at_str.replace("Z", "+00:00")
        updated_at = datetime.fromisoformat(ts_str)
        
        # Ensure updated_at is timezone-aware
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
            
        now = datetime.now(timezone.utc)
        delta = now - updated_at
        days = max(0.0, float(delta.days))
        
        return math.exp(-days / 365.0)
    except Exception as e:
        print(f"Error parsing date '{updated_at_str}': {e}")
        return 0.0

def compute_stars_score(stars: int) -> float:
    """
    Compute stars score using: log10(stars + 1) / log10(100,000)
    Clamped to range [0.0, 1.0]
    """
    if not stars or stars < 0:
        return 0.0
    
    # Calculate log base 10
    log_val = math.log10(stars + 1)
    max_log = math.log10(100000.0) # 5.0
    
    score = log_val / max_log
    return min(1.0, max(0.0, score))

def rank_repositories(merged_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank merged repositories using the formula:
        final_score = 0.4 * semantic_score
                    + 0.3 * keyword_score
                    + 0.2 * log(stars)
                    + 0.1 * recency_score
                    
    Normalization steps:
        - semantic_score: Use vector_similarity directly (range ~ [0.3, 1.0]).
        - keyword_score: Normalize raw keyword_score by max keyword_score in result set.
        - log(stars): Clamped log10(stars + 1) / log10(100k).
        - recency_score: exp(-days / 365).
        
    Returns:
        List of repositories sorted by relevance_score descending.
    """
    if not merged_results:
        return []

    # Find the maximum keyword score to normalize full-text search scores
    max_keyword_score = max([repo.get("keyword_score", 0.0) for repo in merged_results])
    
    ranked_list = []
    
    for repo in merged_results:
        # 1. Semantic score
        semantic_score = repo.get("vector_similarity", 0.0)
        
        # 2. Keyword score (normalize relative to max score in current set)
        raw_keyword = repo.get("keyword_score", 0.0)
        keyword_score = 0.0
        if max_keyword_score > 0:
            keyword_score = raw_keyword / max_keyword_score
            
        # 3. Stars score
        stars = repo.get("stars", 0)
        stars_score = compute_stars_score(stars)
        
        # 4. Recency score
        updated_at = repo.get("updated_at")
        # Handle cases where created_at is provided instead or fall back
        if not updated_at:
            updated_at = repo.get("created_at")
        recency_score = compute_recency_score(updated_at)
        
        # Calculate final combined relevance score
        final_score = (
            0.4 * semantic_score +
            0.3 * keyword_score +
            0.2 * stars_score +
            0.1 * recency_score
        )
        
        # Build final response model item
        ranked_repo = {
            "github_id": repo.get("github_id"),
            "full_name": repo.get("full_name"),
            "description": repo.get("description"),
            "topics": repo.get("topics") or [],
            "language": repo.get("language"),
            "stars": repo.get("stars") or 0,
            "github_url": f"https://github.com/{repo.get('full_name')}",
            "homepage": repo.get("homepage"),
            "relevance_score": round(final_score, 4),
            "updated_at": repo.get("updated_at"),
            # Keep break down for transparency
            "score_breakdown": {
                "semantic": round(semantic_score, 4),
                "keyword": round(keyword_score, 4),
                "stars": round(stars_score, 4),
                "recency": round(recency_score, 4)
            }
        }
        ranked_list.append(ranked_repo)
        
    # Sort final list by relevance_score descending
    ranked_list.sort(key=lambda x: x["relevance_score"], reverse=True)
    return ranked_list
