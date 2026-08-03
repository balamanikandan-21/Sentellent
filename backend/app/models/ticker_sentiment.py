from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class TickerSentiment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ticker_sentiment"

    ticker_symbol: Mapped[str] = mapped_column(
        String(20), ForeignKey("tickers.symbol", ondelete="CASCADE")
    )
    period: Mapped[str] = mapped_column(String(20))
    date: Mapped[dt.date] = mapped_column(Date)
    avg_score: Mapped[float] = mapped_column(Float)
    article_count: Mapped[int] = mapped_column(Integer)
    positive_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    negative_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    neutral_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    __table_args__ = (
        UniqueConstraint("ticker_symbol", "period", "date", name="uq_ticker_sentiment_period"),
    )
