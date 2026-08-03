from __future__ import annotations

import asyncio
import traceback

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session_factory
from app.ingestion.pipeline import run_ingestion

logger = structlog.get_logger()

_running_tasks: dict[str, asyncio.Task] = {}


async def _run_in_background(symbol: str) -> None:
    log = logger.bind(symbol=symbol, task="background_ingestion")
    factory = get_session_factory()

    async with factory() as db:
        try:
            result = await run_ingestion(db, symbol)
            log.info("background_ingestion_done", result=result)
        except Exception as e:
            log.error("background_ingestion_failed", error=str(e), tb=traceback.format_exc())
        finally:
            _running_tasks.pop(symbol.upper(), None)


def trigger_ingestion(symbol: str) -> dict:
    symbol = symbol.upper()

    if symbol in _running_tasks:
        task = _running_tasks[symbol]
        if not task.done():
            return {"status": "already_running", "symbol": symbol}
        _running_tasks.pop(symbol, None)

    task = asyncio.create_task(_run_in_background(symbol))
    _running_tasks[symbol] = task

    return {"status": "started", "symbol": symbol}


def get_ingestion_status(symbol: str) -> dict:
    symbol = symbol.upper()
    task = _running_tasks.get(symbol)

    if task is None:
        return {"status": "idle", "symbol": symbol}

    if task.done():
        _running_tasks.pop(symbol, None)
        if task.exception():
            return {"status": "failed", "symbol": symbol, "error": str(task.exception())}
        return {"status": "completed", "symbol": symbol}

    return {"status": "running", "symbol": symbol}


async def run_ingestion_sync(db: AsyncSession, symbol: str) -> dict:
    return await run_ingestion(db, symbol)
