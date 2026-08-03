import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid_utils import uuid7


class Base(DeclarativeBase):
    pass


def _uuid7() -> uuid.UUID:
    # uuid_utils.uuid7() returns its own `uuid_utils.UUID` type, which is not
    # an instance of the stdlib `uuid.UUID`. SQLAlchemy 2.0's bulk-insert
    # sentinel matching (insertmanyvalues) does an isinstance check on
    # client-generated primary keys and fails silently-then-loudly
    # ("Can't match sentinel values...") whenever 2+ rows are flushed
    # together with a foreign UUID type. Coerce to stdlib uuid.UUID here so
    # every default-generated id is the real thing.
    return uuid.UUID(bytes=uuid7().bytes)


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_uuid7,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
