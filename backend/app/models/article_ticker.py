from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ArticleTicker(Base):
    __tablename__ = "article_tickers"

    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    ticker_symbol: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("tickers.symbol", ondelete="CASCADE"),
        primary_key=True,
    )
