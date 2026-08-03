from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.article_chunk import ArticleChunk
from app.models.article_ticker import ArticleTicker
from app.repositories.base import BaseRepository


class ArticleRepository(BaseRepository[Article]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Article)

    async def get_by_content_hash(self, content_hash: str) -> Article | None:
        stmt = select(Article).where(Article.content_hash == content_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_url(self, url: str) -> Article | None:
        stmt = select(Article).where(Article.url == url)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_ticker(
        self, symbol: str, *, offset: int = 0, limit: int = 50
    ) -> Sequence[Article]:
        stmt = (
            select(Article)
            .join(ArticleTicker, ArticleTicker.article_id == Article.id)
            .where(ArticleTicker.ticker_symbol == symbol.upper())
            .order_by(Article.published_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_similar(
        self, embedding: list[float], *, limit: int = 5, ticker_symbol: str | None = None
    ) -> Sequence[ArticleChunk]:
        from pgvector.sqlalchemy import Vector

        stmt = select(ArticleChunk).order_by(
            ArticleChunk.embedding.cosine_distance(embedding)
        )
        if ticker_symbol:
            stmt = (
                stmt.join(Article, Article.id == ArticleChunk.article_id)
                .join(ArticleTicker, ArticleTicker.article_id == Article.id)
                .where(ArticleTicker.ticker_symbol == ticker_symbol.upper())
            )
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def link_ticker(self, article_id: uuid.UUID, ticker_symbol: str) -> ArticleTicker:
        ticker_symbol = ticker_symbol.upper()
        stmt = select(ArticleTicker).where(
            ArticleTicker.article_id == article_id,
            ArticleTicker.ticker_symbol == ticker_symbol,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        link = ArticleTicker(article_id=article_id, ticker_symbol=ticker_symbol)
        self.session.add(link)
        await self.session.flush()
        return link

    async def create_chunk(
        self,
        article_id: uuid.UUID,
        chunk_index: int,
        content: str,
        embedding: list[float],
        token_count: int,
    ) -> ArticleChunk:
        chunk = ArticleChunk(
            article_id=article_id,
            chunk_index=chunk_index,
            content=content,
            embedding=embedding,
            token_count=token_count,
        )
        self.session.add(chunk)
        await self.session.flush()
        return chunk
