import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import routes
from routes.search import router as search_router

load_dotenv()

app = FastAPI(
    title="GitHub Repository Suggester API",
    description="A semantic and keyword search engine for matching repositories powered by pgvector & Hugging Face",
    version="1.0.0"
)

# Configure CORS so our TanStack Start frontend or other interfaces can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the search router
app.include_router(search_router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the GitHub Repository Suggester API!",
        "docs_url": "/docs",
        "status": "healthy"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting server on {host}:{port}...")
    uvicorn.run("main:app", host=host, port=port, reload=True)
