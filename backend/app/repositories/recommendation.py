from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import Recommendation
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Recommendation)

    async def get_for_user(
        self, user_id: uuid.UUID, *, offset: int = 0, limit: int = 20
    ) -> Sequence[Recommendation]:
        stmt = (
            select(Recommendation)
            .where(Recommendation.user_id == user_id)
            .order_by(Recommendation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_for_ticker(
        self, ticker_symbol: str, *, offset: int = 0, limit: int = 20
    ) -> Sequence[Recommendation]:
        stmt = (
            select(Recommendation)
            .where(Recommendation.ticker_symbol == ticker_symbol.upper())
            .order_by(Recommendation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
