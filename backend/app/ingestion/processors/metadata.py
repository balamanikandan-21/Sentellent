from __future__ import annotations

import re

import structlog

from app.ingestion.config import TICKER_ALIASES

logger = structlog.get_logger()

_SYMBOL_PATTERN = re.compile(r"\b([A-Z]{2,20})\b")


def extract_tickers(text: str, known_symbols: set[str]) -> set[str]:
    found: set[str] = set()
    upper_text = text.upper()

    for symbol in known_symbols:
        if symbol in upper_text:
            found.add(symbol)

    for symbol, aliases in TICKER_ALIASES.items():
        if symbol in known_symbols:
            for alias in aliases:
                if alias.lower() in text.lower():
                    found.add(symbol)
                    break

    return found


def extract_article_metadata(title: str, content: str, source: str) -> dict:
    word_count = len(content.split())

    categories: list[str] = []
    lower = (title + " " + content[:500]).lower()
    if any(w in lower for w in ["earnings", "profit", "revenue", "quarterly", "results"]):
        categories.append("earnings")
    if any(w in lower for w in ["merger", "acquisition", "takeover", "deal"]):
        categories.append("m&a")
    if any(w in lower for w in ["ipo", "listing", "public offer"]):
        categories.append("ipo")
    if any(w in lower for w in ["dividend", "bonus", "buyback", "split"]):
        categories.append("corporate_action")
    if any(w in lower for w in ["upgrade", "downgrade", "target", "rating", "analyst"]):
        categories.append("analyst")
    if any(w in lower for w in ["sensex", "nifty", "market", "index"]):
        categories.append("market")
    if any(w in lower for w in ["rbi", "sebi", "regulation", "policy"]):
        categories.append("regulatory")
    if not categories:
        categories.append("general")

    return {
        "word_count": word_count,
        "categories": categories,
        "source": source,
    }
