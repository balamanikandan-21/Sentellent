from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.auth.dependencies import get_current_user
from app.ingestion.service import get_ingestion_status, trigger_ingestion
from app.models.ingestion_job import IngestionJob
from app.models.user import User

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


class IngestionTriggerRequest(BaseModel):
    symbol: str


class IngestionStatusResponse(BaseModel):
    symbol: str
    status: str
    error: str | None = None


class IngestionJobResponse(BaseModel):
    id: str
    idempotency_key: str
    source: str
    ticker_symbol: str | None
    status: str
    articles_processed: int
    error_message: str | None
    created_at: str
    completed_at: str | None

    class Config:
        from_attributes = True


@router.post("/trigger", response_model=IngestionStatusResponse)
async def trigger(
    body: IngestionTriggerRequest,
    _user: User = Depends(get_current_user),
):
    result = trigger_ingestion(body.symbol)
    return IngestionStatusResponse(
        symbol=result["symbol"],
        status=result["status"],
    )


@router.get("/status/{symbol}", response_model=IngestionStatusResponse)
async def status(
    symbol: str,
    _user: User = Depends(get_current_user),
):
    result = get_ingestion_status(symbol)
    return IngestionStatusResponse(
        symbol=result["symbol"],
        status=result["status"],
        error=result.get("error"),
    )


@router.get("/jobs", response_model=list[IngestionJobResponse])
async def list_jobs(
    symbol: str | None = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    stmt = select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(limit)
    if symbol:
        stmt = stmt.where(IngestionJob.ticker_symbol == symbol.upper())
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    return [
        IngestionJobResponse(
            id=str(j.id),
            idempotency_key=j.idempotency_key,
            source=j.source,
            ticker_symbol=j.ticker_symbol,
            status=j.status,
            articles_processed=j.articles_processed,
            error_message=j.error_message,
            created_at=j.created_at.isoformat() if j.created_at else "",
            completed_at=j.completed_at.isoformat() if j.completed_at else None,
        )
        for j in jobs
    ]
