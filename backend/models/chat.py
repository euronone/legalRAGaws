from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    alpha: Optional[float] = 0.7  # semantic vs keyword weight


class Citation(BaseModel):
    source_file: str
    page_number: int
    citation: str
    relevance_score: float
    text_snippet: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    query: str
