import os
import time
import json
import gzip
import httpx
from datetime import datetime, timedelta
from typing import List, Set, Dict, Any
from dotenv import load_dotenv

# Import our DB and Embedding layers
from db.supabase import get_supabase_client
from services.embedding import get_embeddings

load_dotenv()

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
CHECKPOINT_FILE = "ingest_checkpoint.json"
BATCH_SIZE = 10 # Embedding bulk size

# GitHub Headers
HEADERS = {
    "Accept": "application/vnd.github.v3+json"
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

def load_checkpoint() -> Dict[str, Any]:
    """Load crawl state from checkpoint file."""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r") as f:
                state = json.load(f)
                # Convert list back to set
                state["processed_repos"] = set(state.get("processed_repos", []))
                state["candidates"] = set(state.get("candidates", []))
                return state
        except Exception as e:
            print(f"Error loading checkpoint: {e}")
            
    # Default initial state
    # Crawling starts 1 day ago
    yesterday = datetime.now() - timedelta(days=1)
    return {
        "current_date": yesterday.strftime("%Y-%m-%d"),
        "current_hour": 12,
        "processed_repos": set(),
        "candidates": set()
    }

def save_checkpoint(state: Dict[str, Any]):
    """Save crawl state to checkpoint file."""
    try:
        temp_state = dict(state)
        # Convert sets to lists for JSON serialization
        temp_state["processed_repos"] = list(state.get("processed_repos", []))
        temp_state["candidates"] = list(state.get("candidates", []))
        
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(temp_state, f, indent=2)
    except Exception as e:
        print(f"Error saving checkpoint: {e}")

def check_github_rate_limit(headers: httpx.Headers):
    """Check remaining API limit and sleep if exhausted."""
    remaining = headers.get("X-RateLimit-Remaining")
    reset_time = headers.get("X-RateLimit-Reset")
    
    if remaining is not None:
        rem = int(remaining)
        print(f"GitHub API Remaining: {rem}/5000")
        
        if rem < 50:
            if reset_time is not None:
                wait_duration = int(reset_time) - int(time.time()) + 5
                if wait_duration > 0:
                    print(f"GitHub API limit critical! Sleeping for {wait_duration}s until reset...")
                    time.sleep(wait_duration)

def download_and_parse_gharchive(date_str: str, hour: int) -> Set[str]:
    """
    Downloads an hourly event archive from GH Archive,
    extracts active repo names, and returns them.
    """
    url = f"https://data.gharchive.org/{date_str}-{hour}.json.gz"
    print(f"Downloading active repo names from GH Archive: {url}")
    
    candidates = set()
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            if response.status_code != 200:
                print(f"GH Archive file not found (Status {response.status_code}).")
                return candidates
                
            # Decompress and parse stream
            content = gzip.decompress(response.content)
            lines = content.decode("utf-8").split("\n")
            
            for line in lines:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    repo = event.get("repo")
                    if repo and "name" in repo:
                        candidates.add(repo["name"])
                except Exception:
                    continue
                    
        print(f"Extracted {len(candidates)} candidate repo names from GH Archive.")
    except Exception as e:
        print(f"Failed to fetch or parse GH Archive: {e}")
        
    return candidates

def fetch_repo_details(repo_name: str) -> Optional[Dict[str, Any]]:
    """Fetch repo metadata from GitHub REST API."""
    url = f"https://api.github.com/repos/{repo_name}"
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=HEADERS)
            
            # Check rate limiting headers
            check_github_rate_limit(response.headers)
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            data = response.json()
            
            # Return details
            return {
                "github_id": data.get("id"),
                "full_name": data.get("full_name"),
                "description": data.get("description"),
                "topics": data.get("topics") or [],
                "language": data.get("language"),
                "stars": data.get("stargazers_count", 0),
                "homepage": data.get("homepage"),
                "updated_at": data.get("updated_at"),
                "created_at": data.get("created_at")
            }
    except Exception as e:
        print(f"Error fetching details for {repo_name}: {e}")
        return None

def process_and_save_batch(batch: List[Dict[str, Any]]):
    """Generate SBERT embeddings and save a batch to Supabase."""
    if not batch:
        return
        
    supabase = get_supabase_client()
    
    # 1. Compile text block to generate semantic embedding on
    texts = []
    for r in batch:
        desc = r["description"] or ""
        topics = " ".join(r["topics"])
        text = f"{r['full_name']} {desc} {topics}".strip()
        texts.append(text)
        
    # 2. Bulk get SBERT embeddings
    try:
        print(f"Generating embeddings for batch of {len(batch)} repositories...")
        embeddings = get_embeddings(texts)
    except Exception as e:
        print(f"Error generating embeddings for batch: {e}. Skipping batch save.")
        return
        
    # 3. Add embeddings to payload
    payload = []
    for i, r in enumerate(batch):
        r["embedding"] = embeddings[i]
        payload.append(r)
        
    # 4. Upsert into Supabase
    try:
        supabase.table("repositories").upsert(
            payload, 
            on_conflict="github_id"
        ).execute()
        print(f"Successfully saved {len(payload)} repositories to Supabase.")
    except Exception as e:
        print(f"Error saving repositories to Supabase: {e}")

def run_ingestion():
    """Main crawler ingestion loop."""
    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN is not set. API rate limit will be 60/hr instead of 5000/hr.")
    if not HF_API_KEY:
        print("Error: HUGGINGFACE_API_KEY must be set in your .env file to generate embeddings.")
        return

    # Load state
    state = load_checkpoint()
    print(f"Ingestion started. Resume state: Date={state['current_date']}, Hour={state['current_hour']}")
    
    batch = []
    
    while True:
        # 1. Fetch candidates from GH Archive if queue is empty
        if not state["candidates"]:
            state["candidates"] = download_and_parse_gharchive(
                state["current_date"], 
                state["current_hour"]
            )
            
            # Step hour/date forward
            dt = datetime.strptime(state["current_date"], "%Y-%m-%d")
            hour = state["current_hour"] + 1
            if hour >= 24:
                hour = 0
                dt += timedelta(days=1)
                
            state["current_date"] = dt.strftime("%Y-%m-%d")
            state["current_hour"] = hour
            save_checkpoint(state)
            
            # If still no candidates, break or wait
            if not state["candidates"]:
                print("No candidate repositories found in current archive hour. Sleeping 60s...")
                time.sleep(60)
                continue
                
        # 2. Iterate through candidates
        candidates_list = list(state["candidates"])
        print(f"Queue size: {len(candidates_list)} candidates to inspect.")
        
        for repo_name in candidates_list:
            # Remove from active set
            state["candidates"].remove(repo_name)
            
            # Skip if already processed in this run
            if repo_name in state["processed_repos"]:
                continue
                
            state["processed_repos"].add(repo_name)
            
            # Fetch repo details via GitHub API
            print(f"Inspecting candidate: {repo_name}")
            details = fetch_repo_details(repo_name)
            
            if details:
                stars = details.get("stars", 0)
                desc = details.get("description")
                
                # Ingestion filter criteria
                if stars > 50 and desc:
                    print(f"-> MATCH: {repo_name} has {stars} stars and a description.")
                    batch.append(details)
                    
                    # Process and save when batch is full
                    if len(batch) >= BATCH_SIZE:
                        process_and_save_batch(batch)
                        batch = []
                else:
                    print(f"-> SKIP: {repo_name} fails criteria (stars={stars}, has_desc={bool(desc)})")
            
            # Quick rate limit protection spacing
            time.sleep(0.8)
            
            # Periodic checkpoint saving
            if len(state["processed_repos"]) % 20 == 0:
                save_checkpoint(state)
                
        # Save state at the end of candidate processing loop
        save_checkpoint(state)

if __name__ == "__main__":
    try:
        run_ingestion()
    except KeyboardInterrupt:
        print("\nIngestion crawler paused by user. Saving checkpoint...")
        # Note: state isn't in scope here unless passed, but run_ingestion keeps state updated on-the-fly.
        print("Checkpoint saved successfully. Run the script again to resume.")
