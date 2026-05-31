import os
import time
import httpx
from typing import List, Union
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
MODEL_ID = "sentence-transformers/all-mpnet-base-v2"
API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{MODEL_ID}"

headers = {}
if HF_API_KEY:
    headers["Authorization"] = f"Bearer {HF_API_KEY}"

def get_embeddings(texts: Union[str, List[str]], retries: int = 5, backoff_factor: float = 2.0) -> List[List[float]]:
    """
    Generate embeddings for one or more text snippets using Hugging Face Inference API.
    Handles rate limiting and 503 (Model Loading) errors with exponential backoff.
    
    Returns:
        A list of vector embeddings (list of floats), each of size 768.
    """
    if not HF_API_KEY:
        raise ValueError("HUGGINGFACE_API_KEY is not set. Please set it in your environment variables.")

    is_single = isinstance(texts, str)
    payload_texts = [texts] if is_single else texts

    payload = {
        "inputs": payload_texts,
        "options": {
            "wait_for_model": True  # Instructs HF to wait for the model to load if it's not active
        }
    }

    # Use httpx.Client to perform request
    with httpx.Client(timeout=60.0) as client:
        for attempt in range(retries):
            try:
                response = client.post(API_URL, headers=headers, json=payload)
                
                # Check for model loading (503 Service Unavailable or 200 with "estimated_time" payload)
                if response.status_code == 503 or (response.status_code == 200 and isinstance(response.json(), dict) and "estimated_time" in response.json()):
                    wait_time = backoff_factor ** attempt
                    print(f"Hugging Face model is loading. Retrying in {wait_time}s... (Attempt {attempt + 1}/{retries})")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                embeddings = response.json()
                
                # SBERT inference returns a list of float arrays
                if not isinstance(embeddings, list):
                    raise ValueError(f"Unexpected response format from HF: {embeddings}")
                
                return embeddings
                
            except httpx.HTTPStatusError as e:
                # If we get rate limited or server error, sleep and retry
                if response.status_code in [429, 500, 502, 504]:
                    wait_time = backoff_factor ** attempt
                    print(f"HF API returned status {response.status_code}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"HF API HTTP error: {e.response.text}")
                    raise e
            except Exception as e:
                print(f"Error querying Hugging Face API: {e}")
                if attempt == retries - 1:
                    raise e
                time.sleep(backoff_factor ** attempt)
                
    raise RuntimeError("Failed to fetch embeddings from Hugging Face after maximum retries.")

def get_single_embedding(text: str) -> List[float]:
    """Helper to get embedding for a single text string."""
    embeddings = get_embeddings(text)
    return embeddings[0]
