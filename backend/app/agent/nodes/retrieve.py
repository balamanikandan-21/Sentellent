from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import AgentState
from app.rag.retriever import RAGRetriever
from app.rag.types import SearchFilter
from app.repositories.ticker import TickerRepository

logger = structlog.get_logger()


async def retrieve_documents(state: AgentState, db: AsyncSession) -> AgentState:
    tickers = state.get("tickers_mentioned", [])

    filters = SearchFilter(ticker_symbols=tickers)

    retriever = RAGRetriever(db)
    result = await retriever.retrieve(query=state["query"], filters=filters)

    all_chunks: list[dict] = []
    for chunk in result.chunks:
        all_chunks.append({
            "content": chunk.content,
            "article_id": chunk.article_id,
            "chunk_index": chunk.chunk_index,
            "article_title": chunk.article_title,
            "article_url": chunk.article_url,
            "article_source": chunk.article_source,
            "published_at": chunk.published_at.isoformat() if chunk.published_at else None,
            "sentiment": chunk.sentiment,
            "category": chunk.category,
            "vector_score": chunk.vector_score,
            "keyword_score": chunk.keyword_score,
            "combined_score": chunk.combined_score,
            "rerank_score": chunk.rerank_score,
        })

    all_fundamentals: list[dict] = []
    if tickers:
        ticker_repo = TickerRepository(db)
        for symbol in tickers:
            ticker = await ticker_repo.get_by_symbol(symbol)
            if ticker and ticker.fundamentals:
                all_fundamentals.append({
                    "symbol": ticker.symbol,
                    "company_name": ticker.company_name,
                    "sector": ticker.sector,
                    "fundamentals": ticker.fundamentals,
                })

    logger.info(
        "rag_retrieval_complete",
        chunk_count=len(all_chunks),
        fundamentals_count=len(all_fundamentals),
        confidence=round(result.confidence, 3),
        method=result.retrieval_method,
        candidates=result.candidate_count,
    )

    return {
        **state,
        "retrieved_chunks": all_chunks,
        "ticker_fundamentals": all_fundamentals,
        "retrieval_confidence": result.confidence,
        "retrieval_method": result.retrieval_method,
        "candidate_count": result.candidate_count,
    }
