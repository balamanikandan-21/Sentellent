from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import AgentState, Citation

logger = structlog.get_logger()


async def attach_citations(state: AgentState, db: AsyncSession) -> AgentState:
    chunks = state.get("retrieved_chunks", [])
    if not chunks:
        return {**state, "citations": []}

    seen_articles: set[str] = set()
    citations: list[Citation] = []

    for chunk in chunks:
        article_id = chunk.get("article_id")
        if not article_id or article_id in seen_articles:
            continue
        seen_articles.add(article_id)

        citations.append(
            Citation(
                source_title=chunk.get("article_title", "Unknown"),
                source_url=chunk.get("article_url"),
                source_name=chunk.get("article_source"),
                published_at=chunk.get("published_at"),
                snippet=chunk["content"][:200],
                relevance_score=chunk.get("rerank_score") or chunk.get("combined_score"),
            )
        )

    for f in state.get("ticker_fundamentals", []):
        citations.append(
            Citation(
                source_title=f"Fundamentals: {f['symbol']}",
                source_url=None,
                source_name="yfinance",
                published_at=None,
                snippet=f"{f['company_name']} — Sector: {f.get('sector', 'N/A')}",
                relevance_score=1.0,
            )
        )

    citations.sort(key=lambda c: c.get("relevance_score") or 0, reverse=True)

    logger.info("citations_attached", count=len(citations))
    return {**state, "citations": citations}
