from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.auth.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.ingestion.service import trigger_ingestion
from app.models.user import User
from app.repositories.ticker import TickerRepository

router = APIRouter(prefix="/tickers", tags=["tickers"])


class TickerResponse(BaseModel):
    symbol: str
    company_name: str
    exchange: str
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = None

    class Config:
        from_attributes = True


class FollowResponse(BaseModel):
    symbol: str
    followed: bool
    ingestion_status: str


@router.get("", response_model=list[TickerResponse])
async def list_tickers(
    q: str | None = None,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    repo = TickerRepository(db)
    if q:
        tickers = await repo.search(q, limit=limit)
    else:
        tickers = await repo.list_all(offset=offset, limit=limit)
    return tickers


@router.get("/followed", response_model=list[TickerResponse])
async def get_followed_tickers(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    repo = TickerRepository(db)
    tickers = await repo.get_followed_by_user(user.id)
    return tickers


@router.post("/{symbol}/follow", response_model=FollowResponse)
async def follow_ticker(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    symbol = symbol.upper()
    repo = TickerRepository(db)

    ticker = await repo.get_by_symbol(symbol)
    if not ticker:
        ticker = await repo.upsert(symbol, company_name=symbol, exchange="NSE")

    await repo.follow(user.id, symbol)
    await db.commit()

    result = trigger_ingestion(symbol)

    return FollowResponse(
        symbol=symbol,
        followed=True,
        ingestion_status=result["status"],
    )


@router.delete("/{symbol}/follow")
async def unfollow_ticker(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    symbol = symbol.upper()
    repo = TickerRepository(db)
    removed = await repo.unfollow(user.id, symbol)
    await db.commit()

    if not removed:
        raise NotFoundError("follow", symbol)

    return {"symbol": symbol, "followed": False}


@router.get("/{symbol}", response_model=TickerResponse)
async def get_ticker(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    repo = TickerRepository(db)
    ticker = await repo.get_by_symbol(symbol.upper())
    if not ticker:
        raise NotFoundError("ticker", symbol)
    return ticker
