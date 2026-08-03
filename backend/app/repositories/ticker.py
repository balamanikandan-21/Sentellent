from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticker import Ticker
from app.models.user_ticker import UserTicker


class TickerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_symbol(self, symbol: str) -> Ticker | None:
        return await self.session.get(Ticker, symbol.upper())

    async def search(self, query: str, *, limit: int = 20) -> Sequence[Ticker]:
        stmt = (
            select(Ticker)
            .where(
                Ticker.symbol.ilike(f"%{query}%")
                | Ticker.company_name.ilike(f"%{query}%")
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_all(self, *, offset: int = 0, limit: int = 100) -> Sequence[Ticker]:
        stmt = select(Ticker).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def upsert(self, symbol: str, **kwargs) -> Ticker:
        symbol = symbol.upper()
        ticker = await self.get_by_symbol(symbol)
        if ticker:
            for key, value in kwargs.items():
                setattr(ticker, key, value)
        else:
            ticker = Ticker(symbol=symbol, **kwargs)
            self.session.add(ticker)
        await self.session.flush()
        return ticker

    async def get_followed_by_user(self, user_id: uuid.UUID) -> Sequence[Ticker]:
        stmt = (
            select(Ticker)
            .join(UserTicker, UserTicker.ticker_symbol == Ticker.symbol)
            .where(UserTicker.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def follow(self, user_id: uuid.UUID, symbol: str) -> UserTicker:
        symbol = symbol.upper()
        stmt = select(UserTicker).where(
            UserTicker.user_id == user_id,
            UserTicker.ticker_symbol == symbol,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        ut = UserTicker(user_id=user_id, ticker_symbol=symbol)
        self.session.add(ut)
        await self.session.flush()
        return ut

    async def unfollow(self, user_id: uuid.UUID, symbol: str) -> bool:
        symbol = symbol.upper()
        stmt = delete(UserTicker).where(
            UserTicker.user_id == user_id,
            UserTicker.ticker_symbol == symbol,
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
