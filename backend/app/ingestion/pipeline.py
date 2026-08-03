from __future__ import annotations

import hashlib
import uuid
from contextlib import asynccontextmanager

import structlog
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.db.session import get_engine
from app.ingestion.fetchers.fundamentals import fetch_fundamentals
from app.ingestion.fetchers.news import RawArticle, enrich_article_content, fetch_news
from app.ingestion.processors.chunker import TextChunk, chunk_text
from app.ingestion.processors.dedup import compute_content_hash
from app.ingestion.processors.embeddings import generate_embeddings
from app.ingestion.processors.metadata import extract_article_metadata, extract_tickers
from app.models.article import Article
from app.models.article_chunk import ArticleChunk
from app.models.article_ticker import ArticleTicker
from app.models.fundamentals_chunk import FundamentalsChunk
from app.models.ingestion_job import IngestionJob
from app.models.ticker import Ticker
from app.repositories.article import ArticleRepository
from app.repositories.ingestion import IngestionRepository
from app.repositories.ticker import TickerRepository

logger = structlog.get_logger()


def _idempotency_key(symbol: str, source: str) -> str:
    return f"{source}:{symbol}"


def _advisory_lock_id(symbol: str) -> int:
    return int(hashlib.md5(symbol.encode()).hexdigest()[:15], 16)


@asynccontextmanager
async def _ticker_lock(symbol: str):
    """Hold a session-level advisory lock on a dedicated connection.

    The ingestion pipeline commits mid-run, so a transaction-scoped lock on the
    request session would be released at the first commit. A dedicated
    connection keeps the lock for the entire ingestion and guarantees release
    (explicitly, or by PostgreSQL when the connection closes).
    """
    lock_id = _advisory_lock_id(symbol)
    conn = await get_engine().connect()
    try:
        result = await conn.execute(
            text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": lock_id}
        )
        acquired = bool(result.scalar_one())
        yield acquired
        if acquired:
            await conn.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": lock_id}
            )
    finally:
        await conn.close()


async def _store_fundamentals(
    db: AsyncSession,
    symbol: str,
    fundamentals_data: dict,
) -> None:
    stmt = delete(FundamentalsChunk).where(FundamentalsChunk.ticker_symbol == symbol)
    await db.execute(stmt)

    info = fundamentals_data.get("info", {})
    financials = fundamentals_data.get("financials", {})
    settings = get_settings()

    chunks_to_embed: list[str] = []
    chunk_records: list[dict] = []

    overview = (
        f"{info.get('company_name', symbol)} ({symbol}) — "
        f"Sector: {info.get('sector', 'N/A')}, Industry: {info.get('industry', 'N/A')}. "
        f"Market Cap: {info.get('market_cap_display', 'N/A')}. "
        f"Current Price: {info.get('current_price_display', 'N/A')}. "
        f"P/E Ratio: {info.get('pe_ratio', 'N/A')}, P/B: {info.get('pb_ratio', 'N/A')}. "
        f"EPS: Rs. {info.get('eps', 'N/A')}, Book Value: Rs. {info.get('book_value', 'N/A')}. "
        f"Dividend Yield: {info.get('dividend_yield', 'N/A')}, Beta: {info.get('beta', 'N/A')}. "
        f"52-Week High: Rs. {info.get('52_week_high', 'N/A')}, "
        f"Low: Rs. {info.get('52_week_low', 'N/A')}. "
        f"D/E: {info.get('debt_to_equity', 'N/A')}, ROE: {info.get('return_on_equity', 'N/A')}. "
        f"Revenue: {info.get('revenue_display', 'N/A')}, "
        f"Profit Margin: {info.get('profit_margin', 'N/A')}."
    )
    chunks_to_embed.append(overview)
    chunk_records.append({"chunk_type": "overview", "content": overview, "period": "latest"})

    if info.get("description"):
        chunks_to_embed.append(info["description"])
        chunk_records.append({
            "chunk_type": "description",
            "content": info["description"],
            "period": "latest",
        })

    for stmt_type, stmt_data in financials.items():
        if not stmt_data:
            continue
        lines = [f"{k}: Rs. {v:,.0f}" if isinstance(v, (int, float)) else f"{k}: {v}"
                 for k, v in stmt_data.items() if v is not None]
        text = f"{symbol} {stmt_type.replace('_', ' ').title()}:\n" + "\n".join(lines)

        for chunk in chunk_text(text, chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP):
            chunks_to_embed.append(chunk.content)
            chunk_records.append({
                "chunk_type": stmt_type,
                "content": chunk.content,
                "period": "latest",
            })

    if chunks_to_embed:
        embeddings = await generate_embeddings(chunks_to_embed)
        for record, embedding in zip(chunk_records, embeddings):
            fc = FundamentalsChunk(
                ticker_symbol=symbol,
                chunk_type=record["chunk_type"],
                content=record["content"],
                embedding=embedding,
                period=record["period"],
            )
            db.add(fc)
        await db.flush()

    logger.info("fundamentals_stored", symbol=symbol, chunks=len(chunk_records))


async def _process_article(
    db: AsyncSession,
    article_repo: ArticleRepository,
    raw: RawArticle,
    symbol: str,
    known_symbols: set[str],
    settings,
) -> bool:
    content_hash = compute_content_hash(raw.content)

    existing = await article_repo.get_by_content_hash(content_hash)
    if existing:
        await article_repo.link_ticker(existing.id, symbol)
        return False

    existing_url = await article_repo.get_by_url(raw.url)
    if existing_url:
        await article_repo.link_ticker(existing_url.id, symbol)
        return False

    raw = await enrich_article_content(raw)
    content_hash = compute_content_hash(raw.content)

    existing = await article_repo.get_by_content_hash(content_hash)
    if existing:
        await article_repo.link_ticker(existing.id, symbol)
        return False

    meta = extract_article_metadata(raw.title, raw.content, raw.source)
    meta.update(raw.meta)

    detected_tickers = extract_tickers(raw.title + " " + raw.content, known_symbols)
    detected_tickers.add(symbol)

    article = await article_repo.create(
        url=raw.url,
        title=raw.title,
        source=raw.source,
        content=raw.content,
        content_hash=content_hash,
        published_at=raw.published_at,
        meta=meta,
    )

    for ticker_sym in detected_tickers:
        await article_repo.link_ticker(article.id, ticker_sym)

    chunks: list[TextChunk] = chunk_text(
        raw.content,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )

    if chunks:
        chunk_texts = [c.content for c in chunks]
        embeddings = await generate_embeddings(chunk_texts)

        for chunk, embedding in zip(chunks, embeddings):
            await article_repo.create_chunk(
                article_id=article.id,
                chunk_index=chunk.index,
                content=chunk.content,
                embedding=embedding,
                token_count=chunk.token_count,
            )

    return True


async def run_ingestion(db: AsyncSession, symbol: str) -> dict:
    symbol = symbol.upper()
    log = logger.bind(symbol=symbol)

    async with _ticker_lock(symbol) as locked:
        if not locked:
            log.warning("could_not_acquire_lock")
            return {
                "status": "locked",
                "message": "Another ingestion is running for this ticker",
            }
        return await _run_ingestion_locked(db, symbol, log)


async def _run_ingestion_locked(db: AsyncSession, symbol: str, log) -> dict:
    settings = get_settings()

    ingestion_repo = IngestionRepository(db)
    ticker_repo = TickerRepository(db)
    article_repo = ArticleRepository(db)

    idem_key = _idempotency_key(symbol, "full")
    existing_job = await ingestion_repo.get_by_idempotency_key(idem_key)
    if existing_job and existing_job.status == "running":
        # We hold the ticker lock, so no ingestion is actually running:
        # this is a stale row from a crashed run. Reset and re-run.
        log.warning("resetting_stale_running_job", job_id=str(existing_job.id))

    if existing_job:
        existing_job.status = "pending"
        existing_job.error_message = None
        await db.flush()
        job = existing_job
    else:
        job = await ingestion_repo.create(
            idempotency_key=idem_key,
            source="full",
            ticker_symbol=symbol,
        )

    await ingestion_repo.mark_running(job)
    await db.commit()

    try:
        log.info("fetching_fundamentals")
        fundamentals = await fetch_fundamentals(symbol)

        info = fundamentals["info"]
        ticker = await ticker_repo.upsert(
            symbol,
            company_name=info["company_name"],
            exchange=info.get("exchange", "NSE"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            market_cap=info.get("market_cap"),
            fundamentals=info,
        )
        await db.flush()

        log.info("storing_fundamentals")
        await _store_fundamentals(db, symbol, fundamentals)
        await db.commit()

        log.info("fetching_news")
        raw_articles = await fetch_news(
            symbol, max_articles=settings.MAX_ARTICLES_PER_FEED
        )

        all_ticker_result = await db.execute(select(Ticker.symbol))
        known_symbols = {row[0] for row in all_ticker_result.all()}
        known_symbols.add(symbol)

        new_count = 0
        for raw in raw_articles:
            try:
                is_new = await _process_article(
                    db, article_repo, raw, symbol, known_symbols, settings
                )
                if is_new:
                    new_count += 1

                if new_count % 5 == 0 and new_count > 0:
                    await db.commit()
            except Exception as e:
                log.warning("article_processing_failed", url=raw.url, error=str(e))
                await db.rollback()
                continue

        await ingestion_repo.mark_completed(job, new_count)
        await db.commit()

        result = {
            "status": "completed",
            "job_id": str(job.id),
            "symbol": symbol,
            "articles_processed": new_count,
            "total_fetched": len(raw_articles),
        }
        log.info("ingestion_completed", **result)
        return result

    except Exception as e:
        log.error("ingestion_failed", error=str(e))
        await db.rollback()
        try:
            await ingestion_repo.mark_failed(job, str(e))
            await db.commit()
        except Exception:
            pass
        raise
