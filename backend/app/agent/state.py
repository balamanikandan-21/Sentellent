from __future__ import annotations

import uuid
from typing import TypedDict


class Citation(TypedDict):
    source_title: str
    source_url: str | None
    source_name: str | None
    published_at: str | None
    snippet: str
    relevance_score: float | None


class AgentState(TypedDict, total=False):
    user_id: uuid.UUID
    session_id: uuid.UUID
    query: str
    query_type: str
    tickers_mentioned: list[str]

    retrieved_chunks: list[dict]
    chat_history: list[dict]
    persona: dict | None
    memory_profile: object | None
    ticker_fundamentals: list[dict]

    retrieval_confidence: float
    retrieval_method: str
    candidate_count: int

    analysis: str
    recommendation: dict | None
    citations: list[Citation]
    response: str
    confidence_score: float

    error: str | None
