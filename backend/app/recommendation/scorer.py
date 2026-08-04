from __future__ import annotations

import structlog

from app.recommendation.types import FactorScore

logger = structlog.get_logger()

NIFTY_PE_MEDIAN = 22.0
NIFTY_PB_MEDIAN = 3.5


def _safe_float(data: dict, key: str) -> float | None:
    v = data.get(key)
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def score_fundamentals(info: dict) -> FactorScore:
    pe = _safe_float(info, "pe_ratio")
    pb = _safe_float(info, "pb_ratio")
    roe = _safe_float(info, "return_on_equity")
    margin = _safe_float(info, "profit_margin")
    dte = _safe_float(info, "debt_to_equity")

    available = any(v is not None for v in [pe, pb, roe, margin, dte])
    if not available:
        return FactorScore(
            name="fundamentals",
            score=0.5,
            weight=0.20,
            data_available=False,
            reasoning="No fundamentals data available.",
        )

    signals: list[float] = []
    reasons: list[str] = []
    sources: list[str] = []

    if pe is not None and pe > 0:
        pe_score = max(0, min(1, 1 - (pe - NIFTY_PE_MEDIAN) / (NIFTY_PE_MEDIAN * 2)))
        signals.append(pe_score)
        label = "attractive" if pe < NIFTY_PE_MEDIAN else "elevated"
        reasons.append(f"P/E {pe:.1f} ({label} vs Nifty median ~{NIFTY_PE_MEDIAN})")
        sources.append("Fundamentals")

    if pb is not None and pb > 0:
        pb_score = max(0, min(1, 1 - (pb - NIFTY_PB_MEDIAN) / (NIFTY_PB_MEDIAN * 2)))
        signals.append(pb_score)
        reasons.append(f"P/B {pb:.1f}")
        sources.append("Fundamentals")

    if roe is not None:
        roe_score = max(0, min(1, roe / 0.25))
        signals.append(roe_score)
        label = "strong" if roe > 0.15 else "weak" if roe < 0.08 else "moderate"
        reasons.append(f"ROE {roe:.1%} ({label})")
        sources.append("Fundamentals")

    if margin is not None:
        m_score = max(0, min(1, margin / 0.25))
        signals.append(m_score)
        reasons.append(f"Profit margin {margin:.1%}")
        sources.append("Fundamentals")

    if dte is not None:
        dte_ratio = dte / 100 if dte > 10 else dte
        dte_score = max(0, min(1, 1 - dte_ratio / 2))
        signals.append(dte_score)
        label = "healthy" if dte_ratio < 0.5 else "high" if dte_ratio > 1 else "moderate"
        reasons.append(f"Debt/Equity {dte_ratio:.2f} ({label})")
        sources.append("Fundamentals")

    score = sum(signals) / len(signals) if signals else 0.5
    return FactorScore(
        name="fundamentals",
        score=score,
        weight=0.20,
        data_available=True,
        reasoning="; ".join(reasons),
        sources=list(set(sources)),
    )


def score_momentum(info: dict) -> FactorScore:
    price = _safe_float(info, "current_price")
    high52 = _safe_float(info, "52_week_high")
    low52 = _safe_float(info, "52_week_low")

    if price is None or high52 is None or low52 is None:
        return FactorScore(
            name="momentum",
            score=0.5,
            weight=0.10,
            data_available=False,
            reasoning="Price/52-week range data unavailable.",
        )

    if high52 == low52:
        position = 0.5
    else:
        position = (price - low52) / (high52 - low52)

    if position > 0.9:
        score = 0.7
        label = "near 52-week high — strong trend but limited upside room"
    elif position > 0.6:
        score = 0.8
        label = "upper half of 52-week range — positive momentum"
    elif position > 0.4:
        score = 0.5
        label = "mid-range — neutral momentum"
    elif position > 0.2:
        score = 0.4
        label = "lower range — potential value or weak momentum"
    else:
        score = 0.3
        label = "near 52-week low — weak momentum"

    from app.core.formatting import format_inr

    price_str = format_inr(price) or f"Rs. {price:,.2f}"
    return FactorScore(
        name="momentum",
        score=score,
        weight=0.10,
        data_available=True,
        reasoning=f"Price {price_str} at {position:.0%} of 52W range ({label})",
        sources=["Fundamentals"],
    )


def score_dividend(info: dict) -> FactorScore:
    div_yield = _safe_float(info, "dividend_yield")

    if div_yield is None:
        return FactorScore(
            name="dividend",
            score=0.5,
            weight=0.10,
            data_available=False,
            reasoning="No dividend data available.",
        )

    if div_yield <= 0:
        return FactorScore(
            name="dividend",
            score=0.2,
            weight=0.10,
            data_available=True,
            reasoning="No dividend payout.",
            sources=["Fundamentals"],
        )

    if div_yield > 0.06:
        score = 0.9
        label = "excellent"
    elif div_yield > 0.03:
        score = 0.7
        label = "good"
    elif div_yield > 0.01:
        score = 0.5
        label = "moderate"
    else:
        score = 0.3
        label = "low"

    return FactorScore(
        name="dividend",
        score=score,
        weight=0.10,
        data_available=True,
        reasoning=f"Dividend yield {div_yield:.2%} ({label})",
        sources=["Fundamentals"],
    )


def score_value(info: dict) -> FactorScore:
    pe = _safe_float(info, "pe_ratio")
    pb = _safe_float(info, "pb_ratio")
    eps = _safe_float(info, "eps")
    book_val = _safe_float(info, "book_value")
    price = _safe_float(info, "current_price")

    available = any(v is not None for v in [pe, pb, eps])
    if not available:
        return FactorScore(
            name="value",
            score=0.5,
            weight=0.12,
            data_available=False,
            reasoning="Insufficient valuation data.",
        )

    signals: list[float] = []
    reasons: list[str] = []

    if pe is not None and pe > 0:
        if pe < 15:
            signals.append(0.85)
            reasons.append(f"P/E {pe:.1f} — undervalued territory")
        elif pe < NIFTY_PE_MEDIAN:
            signals.append(0.65)
            reasons.append(f"P/E {pe:.1f} — below market median")
        elif pe < 35:
            signals.append(0.4)
            reasons.append(f"P/E {pe:.1f} — above market median")
        else:
            signals.append(0.2)
            reasons.append(f"P/E {pe:.1f} — overvalued")

    if pb is not None and pb > 0:
        if pb < 1.5:
            signals.append(0.85)
            reasons.append(f"P/B {pb:.1f} — trading near book value")
        elif pb < 3:
            signals.append(0.6)
            reasons.append(f"P/B {pb:.1f} — fair valuation")
        else:
            signals.append(0.3)
            reasons.append(f"P/B {pb:.1f} — premium to book")

    if price is not None and book_val is not None and book_val > 0:
        margin_of_safety = 1 - (price / (book_val * 1.5))
        if margin_of_safety > 0:
            signals.append(0.8)
            reasons.append(f"Margin of safety: {margin_of_safety:.0%}")

    score = sum(signals) / len(signals) if signals else 0.5
    return FactorScore(
        name="value",
        score=score,
        weight=0.12,
        data_available=True,
        reasoning="; ".join(reasons),
        sources=["Fundamentals"],
    )


def score_growth(info: dict, financials: dict | None = None) -> FactorScore:
    roe = _safe_float(info, "return_on_equity")
    margin = _safe_float(info, "profit_margin")
    pe = _safe_float(info, "pe_ratio")

    available = any(v is not None for v in [roe, margin])
    if not available:
        return FactorScore(
            name="growth",
            score=0.5,
            weight=0.12,
            data_available=False,
            reasoning="No growth data available.",
        )

    signals: list[float] = []
    reasons: list[str] = []

    if roe is not None and roe > 0:
        growth_implied = roe * 0.6
        if growth_implied > 0.15:
            signals.append(0.85)
            reasons.append(f"High ROE ({roe:.1%}) implies strong growth potential")
        elif growth_implied > 0.08:
            signals.append(0.6)
            reasons.append(f"Moderate ROE ({roe:.1%}) — decent growth")
        else:
            signals.append(0.35)
            reasons.append(f"Low ROE ({roe:.1%}) — limited growth implied")

    if margin is not None:
        if margin > 0.20:
            signals.append(0.8)
            reasons.append(f"High profit margin ({margin:.1%}) — scalable earnings")
        elif margin > 0.10:
            signals.append(0.6)
            reasons.append(f"Moderate margin ({margin:.1%})")
        elif margin > 0:
            signals.append(0.35)
            reasons.append(f"Thin margin ({margin:.1%}) — limited room for growth")
        else:
            signals.append(0.15)
            reasons.append(f"Negative margin ({margin:.1%}) — loss-making")

    if pe is not None and pe > 30 and roe is not None and roe > 0.2:
        signals.append(0.7)
        reasons.append("High P/E justified by strong ROE — growth premium")

    score = sum(signals) / len(signals) if signals else 0.5
    return FactorScore(
        name="growth",
        score=score,
        weight=0.12,
        data_available=True,
        reasoning="; ".join(reasons),
        sources=["Fundamentals"],
    )


def score_quality(info: dict) -> FactorScore:
    roe = _safe_float(info, "return_on_equity")
    margin = _safe_float(info, "profit_margin")
    dte = _safe_float(info, "debt_to_equity")

    available = any(v is not None for v in [roe, margin, dte])
    if not available:
        return FactorScore(
            name="quality",
            score=0.5,
            weight=0.10,
            data_available=False,
            reasoning="Insufficient quality metrics.",
        )

    signals: list[float] = []
    reasons: list[str] = []

    if roe is not None:
        if roe > 0.20:
            signals.append(0.9)
            reasons.append(f"ROE {roe:.1%} — excellent capital efficiency")
        elif roe > 0.12:
            signals.append(0.65)
            reasons.append(f"ROE {roe:.1%} — good")
        elif roe > 0:
            signals.append(0.35)
            reasons.append(f"ROE {roe:.1%} — below average")
        else:
            signals.append(0.1)
            reasons.append(f"ROE {roe:.1%} — negative returns")

    if margin is not None:
        if margin > 0.20:
            signals.append(0.85)
            reasons.append(f"Margin {margin:.1%} — strong pricing power")
        elif margin > 0.10:
            signals.append(0.6)
            reasons.append(f"Margin {margin:.1%} — healthy")
        elif margin > 0:
            signals.append(0.35)
            reasons.append(f"Margin {margin:.1%} — thin")
        else:
            signals.append(0.1)
            reasons.append(f"Margin {margin:.1%} — loss-making")

    if dte is not None:
        dte_ratio = dte / 100 if dte > 10 else dte
        if dte_ratio < 0.3:
            signals.append(0.9)
            reasons.append(f"D/E {dte_ratio:.2f} — minimal leverage")
        elif dte_ratio < 0.8:
            signals.append(0.65)
            reasons.append(f"D/E {dte_ratio:.2f} — manageable debt")
        elif dte_ratio < 1.5:
            signals.append(0.35)
            reasons.append(f"D/E {dte_ratio:.2f} — elevated")
        else:
            signals.append(0.15)
            reasons.append(f"D/E {dte_ratio:.2f} — highly leveraged")

    score = sum(signals) / len(signals) if signals else 0.5
    return FactorScore(
        name="quality",
        score=score,
        weight=0.10,
        data_available=True,
        reasoning="; ".join(reasons),
        sources=["Fundamentals"],
    )


def score_risk(info: dict) -> FactorScore:
    beta = _safe_float(info, "beta")
    dte = _safe_float(info, "debt_to_equity")
    price = _safe_float(info, "current_price")
    high52 = _safe_float(info, "52_week_high")

    available = any(v is not None for v in [beta, dte])
    if not available:
        return FactorScore(
            name="risk",
            score=0.5,
            weight=0.10,
            data_available=False,
            reasoning="No risk metrics available.",
        )

    signals: list[float] = []
    reasons: list[str] = []

    if beta is not None:
        if beta < 0.8:
            signals.append(0.85)
            reasons.append(f"Beta {beta:.2f} — low volatility, defensive")
        elif beta < 1.2:
            signals.append(0.65)
            reasons.append(f"Beta {beta:.2f} — market-like volatility")
        elif beta < 1.5:
            signals.append(0.4)
            reasons.append(f"Beta {beta:.2f} — above-market volatility")
        else:
            signals.append(0.2)
            reasons.append(f"Beta {beta:.2f} — high volatility")

    if dte is not None:
        dte_ratio = dte / 100 if dte > 10 else dte
        if dte_ratio < 0.5:
            signals.append(0.8)
            reasons.append("Low debt risk")
        elif dte_ratio < 1.0:
            signals.append(0.55)
            reasons.append("Moderate debt risk")
        else:
            signals.append(0.25)
            reasons.append("High leverage risk")

    if price is not None and high52 is not None and high52 > 0:
        drawdown = (high52 - price) / high52
        if drawdown > 0.30:
            signals.append(0.3)
            reasons.append(f"Down {drawdown:.0%} from 52W high — significant drawdown")
        elif drawdown > 0.15:
            signals.append(0.5)
            reasons.append(f"Down {drawdown:.0%} from 52W high")

    score = sum(signals) / len(signals) if signals else 0.5
    return FactorScore(
        name="risk",
        score=score,
        weight=0.10,
        data_available=True,
        reasoning="; ".join(reasons),
        sources=["Fundamentals"],
    )


def score_news_sentiment(
    chunks: list[dict],
    retrieval_confidence: float,
) -> FactorScore:
    if not chunks:
        return FactorScore(
            name="news_sentiment",
            score=0.5,
            weight=0.08,
            data_available=False,
            reasoning="No news articles found in corpus.",
        )

    sentiments = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
    source_names: list[str] = []

    for chunk in chunks:
        sent = (chunk.get("sentiment") or "neutral").lower()
        if sent in sentiments:
            sentiments[sent] += 1
        else:
            sentiments["neutral"] += 1
        if chunk.get("article_title"):
            source_names.append(chunk["article_title"])

    total = sum(sentiments.values())
    if total == 0:
        return FactorScore(
            name="news_sentiment",
            score=0.5,
            weight=0.08,
            data_available=False,
            reasoning="No sentiment data.",
        )

    positive_ratio = sentiments["positive"] / total
    negative_ratio = sentiments["negative"] / total

    score = 0.5 + (positive_ratio - negative_ratio) * 0.4
    score = max(0.1, min(0.9, score))

    parts = []
    if sentiments["positive"]:
        parts.append(f"{sentiments['positive']} positive")
    if sentiments["negative"]:
        parts.append(f"{sentiments['negative']} negative")
    if sentiments["neutral"]:
        parts.append(f"{sentiments['neutral']} neutral")

    unique_sources = list(dict.fromkeys(source_names))[:5]

    return FactorScore(
        name="news_sentiment",
        score=score,
        weight=0.08,
        data_available=True,
        reasoning=f"News sentiment from {total} articles: {', '.join(parts)}",
        sources=unique_sources,
    )


def score_persona_alignment(
    info: dict,
    persona: dict | None,
) -> FactorScore:
    if not persona:
        return FactorScore(
            name="persona_alignment",
            score=0.5,
            weight=0.08,
            data_available=False,
            reasoning="No investor profile available.",
        )

    signals: list[float] = []
    reasons: list[str] = []

    risk_tolerance = (persona.get("risk_tolerance") or "moderate").lower()
    beta = _safe_float(info, "beta")
    div_yield = _safe_float(info, "dividend_yield")
    style = (persona.get("investment_style") or "").lower()

    if beta is not None:
        if risk_tolerance == "conservative" and beta < 1.0:
            signals.append(0.85)
            reasons.append("Low-beta stock aligns with conservative risk profile")
        elif risk_tolerance == "conservative" and beta > 1.3:
            signals.append(0.2)
            reasons.append("High-beta stock conflicts with conservative risk profile")
        elif risk_tolerance == "aggressive" and beta > 1.2:
            signals.append(0.8)
            reasons.append("High-beta stock matches aggressive risk appetite")
        elif risk_tolerance == "aggressive" and beta < 0.7:
            signals.append(0.4)
            reasons.append("Low-beta stock may underperform for aggressive investor")
        else:
            signals.append(0.6)
            reasons.append(f"Beta {beta:.2f} — acceptable for {risk_tolerance} profile")

    if style:
        if "dividend" in style and div_yield is not None:
            if div_yield > 0.02:
                signals.append(0.85)
                reasons.append("Dividend-paying stock matches income-focused style")
            else:
                signals.append(0.3)
                reasons.append("Low/no dividend — not ideal for dividend investor")

        roe = _safe_float(info, "return_on_equity")
        pe = _safe_float(info, "pe_ratio")

        if "value" in style and pe is not None:
            if pe < NIFTY_PE_MEDIAN:
                signals.append(0.8)
                reasons.append("Below-median P/E suits value investing style")
            else:
                signals.append(0.35)
                reasons.append("Above-median P/E — not typical value territory")

        if "growth" in style and roe is not None:
            if roe > 0.18:
                signals.append(0.85)
                reasons.append("High ROE supports growth thesis")
            elif roe > 0.10:
                signals.append(0.55)
                reasons.append("Moderate ROE — some growth potential")

    preferred = persona.get("preferred_tickers") or []
    avoided = persona.get("avoided_tickers") or []
    ticker = (info.get("symbol") or "").upper()

    if ticker and ticker in [t.upper() for t in preferred]:
        signals.append(0.9)
        reasons.append(f"{ticker} is in preferred stocks list")
    elif ticker and ticker in [t.upper() for t in avoided]:
        signals.append(0.1)
        reasons.append(f"{ticker} is in avoided stocks list")

    if not signals:
        return FactorScore(
            name="persona_alignment",
            score=0.5,
            weight=0.08,
            data_available=True,
            reasoning="No specific alignment signals detected.",
        )

    score = sum(signals) / len(signals)
    return FactorScore(
        name="persona_alignment",
        score=score,
        weight=0.08,
        data_available=True,
        reasoning="; ".join(reasons),
    )
