"""
Pydantic models for the GitHub Repository Suggester API.
Covers request validation and structured response shapes.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class SuggestRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=3,
        description="Natural language description of the user's project",
    )
    language: Optional[str] = Field(
        default=None,
        description="Optional programming language filter (e.g. 'Python', 'TypeScript')",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of repo suggestions to return",
    )


class RepoSuggestion(BaseModel):
    rank: int
    repo: str                    # "owner/name"
    relevance_score: float
    why: str                     # Human-readable reason for suggestion
    use_case_fit: str            # How it matches the user's use case
    stars: int
    last_commit: str             # ISO date string


class SuggestResponse(BaseModel):
    intent_summary: str
    suggestions: List[RepoSuggestion]
    follow_up_question: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
