from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class FundamentalsChunk(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "fundamentals_chunks"

    ticker_symbol: Mapped[str] = mapped_column(
        String(20), ForeignKey("tickers.symbol", ondelete="CASCADE"), index=True
    )
    chunk_type: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    period: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
