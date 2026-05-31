from typing import List, Dict, Any
from db.supabase import get_supabase_client

def vector_search(query_embedding: List[float], limit: int = 50, threshold: float = 0.3) -> List[Dict[str, Any]]:
    """
    Perform semantic vector search using the match_repositories Supabase RPC.
    
    Returns:
        List of matching repository records with their cosine similarity.
    """
    supabase = get_supabase_client()
    try:
        response = supabase.rpc(
            "match_repositories",
            {
                "query_embedding": query_embedding,
                "match_threshold": threshold,
                "match_count": limit
            }
        ).execute()
        
        # supabase-py response.data is the returned table
        return response.data or []
    except Exception as e:
        print(f"Error during vector search RPC: {e}")
        # Return empty list on failure so the program degrades gracefully
        return []

def keyword_search(query_text: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Perform full-text search on description and topics using the keyword_search_repositories Supabase RPC.
    
    Returns:
        List of matching repository records with their keyword_score (ts_rank).
    """
    supabase = get_supabase_client()
    # Strip special SQL characters to avoid query injection, though websearch_to_tsquery is safe
    sanitized_query = query_text.strip()
    if not sanitized_query:
        return []
        
    try:
        response = supabase.rpc(
            "keyword_search_repositories",
            {
                "query_text": sanitized_query,
                "match_count": limit
            }
        ).execute()
        
        return response.data or []
    except Exception as e:
        print(f"Error during keyword search RPC: {e}")
        return []
