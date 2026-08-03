from __future__ import annotations

import json
from datetime import date

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import AgentState
from app.config.settings import get_settings
from app.models.ticker_sentiment import TickerSentiment

logger = structlog.get_logger()

SENTIMENT_SCORE_PROMPT = """\
Rate the overall sentiment of this analysis about {ticker} on a scale from \
-1.0 (very bearish) to +1.0 (very bullish). Return ONLY a JSON object:
{{"score": <float>, "label": "bullish|bearish|neutral"}}

Analysis:
{analysis}
"""


async def update_sentiment(state: AgentState, db: AsyncSession) -> AgentState:
    query_type = state.get("query_type", "research")
    tickers = state.get("tickers_mentioned", [])
    analysis = state.get("analysis", "")

    if query_type not in ("sentiment", "research", "recommendation") or not tickers or not analysis:
        return state

    settings = get_settings()
    llm = ChatAnthropic(
        model=settings.TAGGING_MODEL,
        api_key=settings.ANTHROPIC_API_KEY,
        max_tokens=128,
        temperature=0,
    )

    for ticker in tickers[:3]:
        try:
            response = await llm.ainvoke([
                SystemMessage(content="You score sentiment."),
                HumanMessage(
                    content=SENTIMENT_SCORE_PROMPT.format(ticker=ticker, analysis=analysis[:2000])
                ),
            ])

            result = json.loads(response.content)
            score = float(result.get("score", 0))
            label = result.get("label", "neutral")

            stmt = select(TickerSentiment).where(
                TickerSentiment.ticker_symbol == ticker.upper(),
                TickerSentiment.period == "daily",
                TickerSentiment.date == date.today(),
            )
            existing = (await db.execute(stmt)).scalar_one_or_none()

            if existing:
                count = existing.article_count + 1
                existing.avg_score = (
                    (existing.avg_score * existing.article_count) + score
                ) / count
                existing.article_count = count
                if label == "bullish":
                    existing.positive_count += 1
                elif label == "bearish":
                    existing.negative_count += 1
                else:
                    existing.neutral_count += 1
            else:
                sentiment = TickerSentiment(
                    ticker_symbol=ticker.upper(),
                    period="daily",
                    date=date.today(),
                    avg_score=score,
                    article_count=1,
                    positive_count=1 if label == "bullish" else 0,
                    negative_count=1 if label == "bearish" else 0,
                    neutral_count=1 if label == "neutral" else 0,
                )
                db.add(sentiment)

            await db.commit()
            logger.info("sentiment_updated", ticker=ticker, score=score, label=label)

        except Exception:
            logger.exception("sentiment_update_failed", ticker=ticker)

    return state
