from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time

# Import our services
from services.embedding import get_single_embedding
from services.search import vector_search, keyword_search
from services.fusion import reciprocal_rank_fusion
from services.ranking import rank_repositories
from services.github import search_github_live, save_repositories_background

router = APIRouter(prefix="/api/v1")

# Pydantic models for request validation
class SearchRequest(BaseModel):
    description: str = Field(..., min_length=3, description="Description of the project/query")
    tech_stack: List[str] = Field(default=[], description="List of technologies (e.g. ['React', 'Python'])")
    page: Optional[int] = Field(default=1, ge=1, description="Page number for pagination")

class FallbackRequest(BaseModel):
    description: str = Field(..., min_length=3)
    tech_stack: List[str] = Field(default=[])

# Simple dict-based in-memory cache
# Key format: (description, tuple(sorted(tech_stack)), page) -> (timestamp, response_data)
CACHE_TTL = 300 # 5 minutes TTL
_search_cache: Dict[tuple, tuple] = {}
MAX_CACHE_SIZE = 1000

def get_cached_results(cache_key: tuple) -> Optional[List[Dict[str, Any]]]:
    """Retrieve items from cache if not expired."""
    if cache_key in _search_cache:
        timestamp, data = _search_cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            return data
        # Evict expired entry
        del _search_cache[cache_key]
    return None

def set_cached_results(cache_key: tuple, data: List[Dict[str, Any]]):
    """Store results in cache, maintaining max capacity."""
    global _search_cache
    if len(_search_cache) >= MAX_CACHE_SIZE:
        # Clear out oldest 100 entries
        sorted_keys = sorted(_search_cache.keys(), key=lambda k: _search_cache[k][0])
        for k in sorted_keys[:100]:
            del _search_cache[k]
            
    _search_cache[cache_key] = (time.time(), data)

@router.post("/search")
def search_repositories_api(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    Search database for matching repositories.
    Combines pgvector similarity and full-text keyword search via RRF.
    If results count < 5, fallback to live GitHub API search and save new repos.
    """
    # 1. Create cache key
    cache_key = (
        request.description.strip().lower(), 
        tuple(sorted([t.strip().lower() for t in request.tech_stack])), 
        request.page
    )
    
    # 2. Check cache
    cached_response = get_cached_results(cache_key)
    if cached_response is not None:
        print("Search Cache Hit!")
        return {"results": cached_response, "source": "cache"}

    # 3. Perform search flow
    query_text = request.description.strip()
    if request.tech_stack:
        query_text += " " + " ".join(request.tech_stack)

    print(f"Searching database for: '{query_text}' (page {request.page})")

    # A. Get query embedding
    try:
        query_embedding = get_single_embedding(query_text)
    except Exception as e:
        # If Hugging Face is completely down, log it but don't fail, we'll rely on text search and fallback
        print(f"HF embedding error: {e}")
        query_embedding = []

    # B. Vector Search
    vector_results = []
    if query_embedding:
        # Fetch top 50 semantic matches
        vector_results = vector_search(query_embedding, limit=50)

    # C. Keyword Search
    # Fetch top 50 text matches
    keyword_results = keyword_search(query_text, limit=50)

    # D. Reciprocal Rank Fusion
    merged = reciprocal_rank_fusion(vector_results, keyword_results, k=60)

    # E. Final Rank Calculation
    ranked = rank_repositories(merged)

    # 4. Check if results < 5 -> Fallback to live GitHub Search
    source = "database"
    if len(ranked) < 5:
        print(f"Found only {len(ranked)} results in DB. Triggering live GitHub fallback...")
        fallback_repos = search_github_live(request.description, request.tech_stack)
        
        if fallback_repos:
            # Trigger background task to embed and cache new repos in Supabase
            background_tasks.add_task(save_repositories_background, fallback_repos)
            
            # Since these fallback repos are new, compute their on-the-fly ranking
            # To rank them correctly, generate embeddings on the fly for returned repos
            texts_to_embed = [
                f"{r['full_name']} {r.get('description') or ''} {' '.join(r.get('topics') or [])}"
                for r in fallback_repos
            ]
            
            try:
                embeddings = get_single_embedding(query_text) # Query embedding
                repo_embeddings = get_embeddings(texts_to_embed) if texts_to_embed else []
                
                # Setup structures to allow rank_repositories to run on them
                fallback_merged = []
                for idx, r in enumerate(fallback_repos):
                    # Compute cosine similarity manually for fallback repos using query_embedding
                    sim = 0.5 # Default similarity if generation fails
                    if idx < len(repo_embeddings) and query_embedding:
                        # Vector dot product normalized
                        v1 = query_embedding
                        v2 = repo_embeddings[idx]
                        dot = sum(a*b for a,b in zip(v1, v2))
                        n1 = sum(a*a for a in v1) ** 0.5
                        n2 = sum(a*a for a in v2) ** 0.5
                        sim = dot / (n1 * n2) if n1 * n2 > 0 else 0.5
                    
                    fallback_merged.append({
                        **r,
                        "vector_similarity": sim,
                        "keyword_score": 1.0 # Give default text match weight
                    })
                
                # Rank them
                ranked = rank_repositories(fallback_merged)
                source = "github_fallback"
            except Exception as e:
                print(f"Error ranking live fallback results on-the-fly: {e}")
                # Simple fallback ranking
                ranked = []
                for r in fallback_repos:
                    ranked.append({
                        "github_id": r["github_id"],
                        "full_name": r["full_name"],
                        "description": r["description"],
                        "topics": r["topics"],
                        "language": r["language"],
                        "stars": r["stars"],
                        "github_url": f"https://github.com/{r['full_name']}",
                        "homepage": r["homepage"],
                        "relevance_score": 0.5,
                        "updated_at": r["updated_at"]
                    })
                source = "github_fallback_simple"

    # 5. Handle Pagination (20 items per page)
    PAGE_SIZE = 20
    start_idx = (request.page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    paginated_results = ranked[start_idx:end_idx]

    # 6. Cache and return
    set_cached_results(cache_key, paginated_results)
    
    return {
        "results": paginated_results,
        "total_results": len(ranked),
        "page": request.page,
        "source": source
    }

@router.post("/search/fallback")
def fallback_search_api(request: FallbackRequest, background_tasks: BackgroundTasks):
    """
    Direct endpoint to perform live GitHub search and automatically cache the results in the database.
    """
    print(f"Direct GitHub Live search fallback requested for: description='{request.description}', tech_stack={request.tech_stack}")
    
    fallback_repos = search_github_live(request.description, request.tech_stack)
    
    if not fallback_repos:
        return {"results": [], "source": "github_direct"}
        
    # Queue up background task to generate embeddings and save
    background_tasks.add_task(save_repositories_background, fallback_repos)
    
    # Return formatted results
    formatted_results = []
    for r in fallback_repos:
        formatted_results.append({
            "github_id": r["github_id"],
            "full_name": r["full_name"],
            "description": r["description"],
            "topics": r["topics"],
            "language": r["language"],
            "stars": r["stars"],
            "github_url": f"https://github.com/{r['full_name']}",
            "homepage": r["homepage"],
            "relevance_score": 1.0, # Default direct match score
            "updated_at": r["updated_at"]
        })
        
    return {
        "results": formatted_results,
        "total_results": len(formatted_results),
        "source": "github_direct"
    }
