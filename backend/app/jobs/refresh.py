"""Scheduled news + fundamentals refresh for every followed ticker.

Run as a one-off container (EventBridge Scheduler -> ECS run-task):

    python -m app.jobs.refresh

Ingestion is idempotent (content-hash dedup + per-ticker advisory locks), so
overlapping with a user-triggered ingestion is safe: the scheduled run simply
skips tickers that are locked.
"""

from __future__ import annotations

import asyncio

import structlog
from sqlalchemy import distinct, select

from app.core.logging import setup_logging
from app.db.session import get_engine, get_session_factory
from app.ingestion.pipeline import run_ingestion
from app.models.user_ticker import UserTicker

logger = structlog.get_logger()


async def refresh_all_followed() -> dict:
    factory = get_session_factory()

    async with factory() as db:
        result = await db.execute(select(distinct(UserTicker.ticker_symbol)))
        symbols = sorted({row[0] for row in result.all()})

    log = logger.bind(job="scheduled_refresh", tickers=len(symbols))
    log.info("refresh_started", symbols=symbols)

    outcomes: dict[str, str] = {}
    for symbol in symbols:
        async with factory() as db:
            try:
                result = await run_ingestion(db, symbol)
                outcomes[symbol] = result.get("status", "unknown")
            except Exception as e:
                log.error("refresh_ticker_failed", symbol=symbol, error=str(e))
                outcomes[symbol] = "failed"

    log.info("refresh_finished", outcomes=outcomes)
    return outcomes


async def _main() -> None:
    setup_logging()
    try:
        await refresh_all_followed()
    finally:
        await get_engine().dispose()


if __name__ == "__main__":
    asyncio.run(_main())
