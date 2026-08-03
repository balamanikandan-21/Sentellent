from __future__ import annotations

import asyncio
from typing import Any

import structlog
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.formatting import format_inr as _format_inr
from app.ingestion.config import NSE_EXCHANGE_SUFFIX

logger = structlog.get_logger()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _fetch_yfinance(symbol: str) -> dict[str, Any]:
    yf_symbol = f"{symbol}{NSE_EXCHANGE_SUFFIX}"
    ticker = yf.Ticker(yf_symbol)
    info = ticker.info

    if not info or info.get("regularMarketPrice") is None:
        raise ValueError(f"No data returned for {yf_symbol}")

    financials = {}
    try:
        inc = ticker.income_stmt
        if inc is not None and not inc.empty:
            latest = inc.iloc[:, 0]
            financials["income_statement"] = {
                str(k): float(v) if v == v else None  # noqa: PLR0124 — NaN check
                for k, v in latest.items()
            }
    except Exception:
        pass

    try:
        bs = ticker.balance_sheet
        if bs is not None and not bs.empty:
            latest = bs.iloc[:, 0]
            financials["balance_sheet"] = {
                str(k): float(v) if v == v else None
                for k, v in latest.items()
            }
    except Exception:
        pass

    return {
        "info": {
            "company_name": info.get("longName") or info.get("shortName", symbol),
            "exchange": info.get("exchange", "NSE"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "market_cap_display": _format_inr(info.get("marketCap")),
            "current_price": info.get("regularMarketPrice"),
            "current_price_display": _format_inr(info.get("regularMarketPrice")),
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "dividend_yield": info.get("dividendYield"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "eps": info.get("trailingEps"),
            "book_value": info.get("bookValue"),
            "debt_to_equity": info.get("debtToEquity"),
            "return_on_equity": info.get("returnOnEquity"),
            "revenue": info.get("totalRevenue"),
            "revenue_display": _format_inr(info.get("totalRevenue")),
            "profit_margin": info.get("profitMargins"),
            "currency": "INR",
            "description": info.get("longBusinessSummary"),
        },
        "financials": financials,
    }


async def fetch_fundamentals(symbol: str) -> dict[str, Any]:
    logger.info("fetching_fundamentals", symbol=symbol)
    data = await asyncio.to_thread(_fetch_yfinance, symbol)
    logger.info("fundamentals_fetched", symbol=symbol, has_financials=bool(data.get("financials")))
    return data
