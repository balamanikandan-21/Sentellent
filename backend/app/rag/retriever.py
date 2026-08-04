from __future__ import annotations

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.ingestion.processors.embeddings import generate_single_embedding
from app.rag.confidence import compute_confidence
from app.rag.reranker import rerank_chunks
from app.rag.types import RetrievalResult, RetrievedChunk, SearchFilter

logger = structlog.get_logger()


class RAGRetriever:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def retrieve(
        self,
        query: str,
        filters: SearchFilter | None = None,
    ) -> RetrievalResult:
        settings = get_settings()
        filters = filters or SearchFilter()

        query_embedding = await generate_single_embedding(query)

        candidates = await self._hybrid_search(
            query=query,
            embedding=query_embedding,
            filters=filters,
            candidate_k=settings.RAG_CANDIDATE_K,
            alpha=settings.HYBRID_ALPHA,
        )

        if not candidates:
            logger.info("retrieval_empty", query=query[:80])
            return RetrievalResult(
                chunks=[],
                confidence=0.0,
                retrieval_method="hybrid",
                candidate_count=0,
                query_tokens=0,
            )

        reranked = await rerank_chunks(
            query=query,
            chunks=candidates,
            top_k=settings.RAG_RERANK_K,
        )

        confidence = compute_confidence(reranked, len(candidates))

        logger.info(
            "retrieval_complete",
            query=query[:80],
            candidates=len(candidates),
            reranked=len(reranked),
            confidence=round(confidence, 3),
        )

        return RetrievalResult(
            chunks=reranked,
            confidence=confidence,
            retrieval_method="hybrid+rerank",
            candidate_count=len(candidates),
            query_tokens=0,
        )

    async def _hybrid_search(
        self,
        query: str,
        embedding: list[float],
        filters: SearchFilter,
        candidate_k: int,
        alpha: float,
    ) -> list[RetrievedChunk]:
        where_clauses: list[str] = []
        params: dict = {
            "embedding": str(embedding),
            "query_text": query,
            "candidate_k": candidate_k,
            "alpha": alpha,
        }

        if filters.ticker_symbols:
            where_clauses.append("at.ticker_symbol = ANY(:ticker_symbols)")
            params["ticker_symbols"] = [s.upper() for s in filters.ticker_symbols]

        if filters.sources:
            where_clauses.append("a.source = ANY(:sources)")
            params["sources"] = filters.sources

        if filters.date_from:
            where_clauses.append("a.published_at >= :date_from")
            params["date_from"] = filters.date_from

        if filters.date_to:
            where_clauses.append("a.published_at <= :date_to")
            params["date_to"] = filters.date_to

        if filters.sentiment:
            where_clauses.append("a.sentiment = :sentiment")
            params["sentiment"] = filters.sentiment

        if filters.categories:
            where_clauses.append("a.metadata->>'category' = ANY(:categories)")
            params["categories"] = filters.categories

        ticker_join = ""
        if filters.ticker_symbols:
            ticker_join = "JOIN article_tickers at ON at.article_id = a.id"

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        sql = text(f"""
            WITH vector_search AS (
                SELECT
                    ac.id AS chunk_id,
                    ac.article_id,
                    ac.chunk_index,
                    ac.content,
                    a.title AS article_title,
                    a.url AS article_url,
                    a.source AS article_source,
                    a.published_at,
                    a.sentiment,
                    a.metadata->>'category' AS category,
                    1 - (ac.embedding <=> CAST(:embedding AS vector)) AS vector_sim
                FROM article_chunks ac
                JOIN articles a ON a.id = ac.article_id
                {ticker_join}
                {where_sql}
                ORDER BY ac.embedding <=> CAST(:embedding AS vector)
                LIMIT :candidate_k
            ),
            keyword_search AS (
                SELECT
                    ac.id AS chunk_id,
                    ts_rank_cd(
                        to_tsvector('english', ac.content),
                        plainto_tsquery('english', :query_text)
                    ) AS kw_rank
                FROM article_chunks ac
                JOIN articles a ON a.id = ac.article_id
                {ticker_join}
                {where_sql}
                  {"AND" if where_clauses else "WHERE"}
                  to_tsvector('english', ac.content) @@ plainto_tsquery('english', :query_text)
                LIMIT :candidate_k
            )
            SELECT
                vs.chunk_id,
                vs.article_id,
                vs.chunk_index,
                vs.content,
                vs.article_title,
                vs.article_url,
                vs.article_source,
                vs.published_at,
                vs.sentiment,
                vs.category,
                vs.vector_sim,
                COALESCE(ks.kw_rank, 0) AS kw_rank,
                (:alpha * vs.vector_sim + (1 - :alpha) * COALESCE(ks.kw_rank, 0)) AS combined
            FROM vector_search vs
            LEFT JOIN keyword_search ks ON ks.chunk_id = vs.chunk_id
            ORDER BY combined DESC
            LIMIT :candidate_k
        """)

        result = await self.db.execute(sql, params)
        rows = result.fetchall()

        chunks: list[RetrievedChunk] = []
        for row in rows:
            chunks.append(
                RetrievedChunk(
                    content=row.content,
                    article_id=str(row.article_id),
                    chunk_index=row.chunk_index,
                    article_title=row.article_title,
                    article_url=row.article_url,
                    article_source=row.article_source,
                    published_at=row.published_at,
                    sentiment=row.sentiment,
                    category=row.category,
                    vector_score=float(row.vector_sim),
                    keyword_score=float(row.kw_rank),
                    combined_score=float(row.combined),
                )
            )

        logger.info(
            "hybrid_search_done",
            total=len(chunks),
            with_keyword_match=sum(1 for c in chunks if c.keyword_score > 0),
        )
        return chunks
