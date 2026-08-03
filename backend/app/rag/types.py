from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SearchFilter:
    ticker_symbols: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    date_from: datetime | None = None
    date_to: datetime | None = None
    sentiment: str | None = None
    categories: list[str] = field(default_factory=list)


@dataclass
class RetrievedChunk:
    content: str
    article_id: str
    chunk_index: int
    article_title: str
    article_url: str
    article_source: str
    published_at: datetime | None
    sentiment: str | None
    category: str | None
    vector_score: float
    keyword_score: float
    combined_score: float
    rerank_score: float | None = None


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    confidence: float
    retrieval_method: str
    candidate_count: int
    query_tokens: int

    @property
    def has_sufficient_context(self) -> bool:
        return self.confidence >= 0.35 and len(self.chunks) > 0
