import os
import httpx
from typing import List, Dict, Any
from dotenv import load_dotenv
from db.supabase import get_supabase_client
from services.embedding import get_embeddings

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Accept": "application/vnd.github.v3+json"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

def search_github_live(description: str, tech_stack: List[str]) -> List[Dict[str, Any]]:
    """
    Search GitHub REST API live for repositories matching the query description and tech stack.
    """
    # Build query string
    keywords = description.strip()
    # Add language filters or tech stack keyword queries
    tech_query = " ".join(tech_stack)
    query = f"{keywords} {tech_query}".strip()
    
    if not query:
        return []
        
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=15"
    
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, headers=HEADERS)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            parsed_repos = []
            for item in items:
                parsed_repos.append({
                    "github_id": item.get("id"),
                    "full_name": item.get("full_name"),
                    "description": item.get("description"),
                    "topics": item.get("topics") or [],
                    "language": item.get("language"),
                    "stars": item.get("stargazers_count", 0),
                    "homepage": item.get("homepage"),
                    "updated_at": item.get("updated_at"),
                    "created_at": item.get("created_at")
                })
            return parsed_repos
            
    except Exception as e:
        print(f"Error searching GitHub live: {e}")
        return []

def save_repositories_background(repos: List[Dict[str, Any]]):
    """
    Background task to generate embeddings for newly crawled repositories
    and insert/upsert them into Supabase.
    """
    if not repos:
        return
        
    supabase = get_supabase_client()
    
    # 1. Extract texts to embed
    texts_to_embed = []
    valid_repos = []
    
    for repo in repos:
        desc = repo.get("description") or ""
        topics = " ".join(repo.get("topics") or [])
        text = f"{repo['full_name']} {desc} {topics}".strip()
        texts_to_embed.append(text)
        valid_repos.append(repo)
        
    if not texts_to_embed:
        return
        
    # 2. Bulk generate embeddings
    try:
        embeddings = get_embeddings(texts_to_embed)
    except Exception as e:
        print(f"Failed to generate embeddings in background: {e}")
        return

    # 3. Prep data for Supabase upsert
    db_payload = []
    for i, repo in enumerate(valid_repos):
        db_payload.append({
            "github_id": repo["github_id"],
            "full_name": repo["full_name"],
            "description": repo["description"],
            "topics": repo["topics"],
            "language": repo["language"],
            "stars": repo["stars"],
            "homepage": repo["homepage"],
            "embedding": embeddings[i],
            "updated_at": repo["updated_at"],
            "created_at": repo["created_at"]
        })
        
    # 4. Upsert into Supabase (violating unique constraint will update)
    try:
        # Use upsert in Supabase to insert new or update existing
        supabase.table("repositories").upsert(
            db_payload, 
            on_conflict="github_id"
        ).execute()
        print(f"Successfully cached {len(db_payload)} fallback repos in Supabase.")
    except Exception as e:
        print(f"Failed to upsert fallback repositories to Supabase: {e}")
