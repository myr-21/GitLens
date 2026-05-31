from typing import List, Dict, Any

def reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]], 
    keyword_results: List[Dict[str, Any]], 
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    Merge semantic vector search results and keyword full-text search results
    using Reciprocal Rank Fusion (RRF).
    
    Formula:
        RRF_Score(d) = sum(1 / (k + rank_m(d))) for each list m containing d
        
    Returns:
        A list of merged repository dicts, ordered by their RRF score descending.
        Each merged dict retains metadata and stores its ranks/scores from both searches.
    """
    rrf_scores = {}
    repo_map = {}

    # Helper to process a results list and compute its RRF component
    def process_list(results: List[Dict[str, Any]], list_name: str, score_key: str):
        for rank, repo in enumerate(results, start=1):
            github_id = repo["github_id"]
            
            if github_id not in repo_map:
                # Store full repo dictionary copy to avoid side-effects
                repo_map[github_id] = dict(repo)
                # Initialize rank and score placeholders
                repo_map[github_id]["vector_rank"] = None
                repo_map[github_id]["vector_similarity"] = 0.0
                repo_map[github_id]["keyword_rank"] = None
                repo_map[github_id]["keyword_score"] = 0.0
            
            # Update specific rank and score
            if list_name == "vector":
                repo_map[github_id]["vector_rank"] = rank
                repo_map[github_id]["vector_similarity"] = repo.get("similarity", 0.0)
            elif list_name == "keyword":
                repo_map[github_id]["keyword_rank"] = rank
                repo_map[github_id]["keyword_score"] = repo.get("keyword_score", 0.0)
                
            # Add to RRF score
            rrf_scores[github_id] = rrf_scores.get(github_id, 0.0) + (1.0 / (k + rank))

    # Process vector and keyword results
    process_list(vector_results, "vector", "similarity")
    process_list(keyword_results, "keyword", "keyword_score")

    # Attach RRF score to each repo dict
    merged_results = []
    for github_id, repo in repo_map.items():
        repo["rrf_score"] = rrf_scores[github_id]
        merged_results.append(repo)

    # Sort merged results by RRF score descending
    merged_results.sort(key=lambda x: x["rrf_score"], reverse=True)
    
    return merged_results
