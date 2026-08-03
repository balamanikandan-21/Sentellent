from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import mktime

import feedparser
import httpx
import structlog
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from app.ingestion.config import RSS_FEEDS, ticker_news_feeds

logger = structlog.get_logger()


@dataclass
class RawArticle:
    url: str
    title: str
    source: str
    content: str
    published_at: datetime | None = None
    meta: dict = field(default_factory=dict)


def _parse_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def _extract_entry_content(entry: dict) -> str:
    if hasattr(entry, "content") and entry.content:
        return _parse_html(entry.content[0].get("value", ""))
    if hasattr(entry, "summary") and entry.summary:
        return _parse_html(entry.summary)
    if hasattr(entry, "description") and entry.description:
        return _parse_html(entry.description)
    return entry.get("title", "")


def _parse_published(entry: dict) -> datetime | None:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime.fromtimestamp(mktime(entry.updated_parsed), tz=timezone.utc)
    return None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def _fetch_feed(feed_url: str, feed_name: str, max_articles: int) -> list[RawArticle]:
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(feed_url, headers={"User-Agent": "SentellentBot/1.0"})
        resp.raise_for_status()

    parsed = await asyncio.to_thread(feedparser.parse, resp.text)
    articles: list[RawArticle] = []

    for entry in parsed.entries[:max_articles]:
        url = entry.get("link", "")
        if not url:
            continue

        content = _extract_entry_content(entry)
        if len(content) < 50:
            continue

        articles.append(
            RawArticle(
                url=url,
                title=entry.get("title", "Untitled"),
                source=feed_name,
                content=content,
                published_at=_parse_published(entry),
                meta={
                    "author": entry.get("author"),
                    "tags": [t.get("term") for t in entry.get("tags", []) if t.get("term")],
                },
            )
        )

    return articles


async def _try_fetch_full_article(url: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "SentellentBot/1.0"})
            resp.raise_for_status()
        text = _parse_html(resp.text)
        if len(text) > 200:
            return text
    except Exception:
        pass
    return None


async def fetch_news(
    symbol: str, *, max_articles: int = 50, company_name: str | None = None
) -> list[RawArticle]:
    # Ticker-specific news first (Google News search), then broad market feeds
    # for context. Without the former the corpus has almost no coverage of the
    # followed stock and retrieval confidence stays below threshold.
    feed_configs = ticker_news_feeds(symbol, company_name) + RSS_FEEDS.get(
        symbol, RSS_FEEDS["_default"]
    )
    logger.info("fetching_news", symbol=symbol, feed_count=len(feed_configs))

    tasks = [
        _fetch_feed(fc["url"], fc["name"], max_articles)
        for fc in feed_configs
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    articles: list[RawArticle] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(
                "feed_fetch_failed",
                feed=feed_configs[i]["name"],
                error=str(result),
            )
            continue
        articles.extend(result)

    logger.info("news_fetched", symbol=symbol, total_articles=len(articles))
    return articles


async def enrich_article_content(article: RawArticle) -> RawArticle:
    if len(article.content) < 300:
        full = await _try_fetch_full_article(article.url)
        if full:
            article.content = full
    return article
