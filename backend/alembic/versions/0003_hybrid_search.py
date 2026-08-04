"""add tsvector column and GIN index for hybrid search

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-01
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE article_chunks "
        "ADD COLUMN IF NOT EXISTS search_vector tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', content)) STORED"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_article_chunks_search_vector "
        "ON article_chunks USING GIN (search_vector)"
    )

    op.execute("CREATE INDEX IF NOT EXISTS ix_articles_source ON articles (source)")

    op.execute("CREATE INDEX IF NOT EXISTS ix_articles_published_at ON articles (published_at)")

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_articles_sentiment "
        "ON articles (sentiment) WHERE sentiment IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_articles_sentiment")
    op.execute("DROP INDEX IF EXISTS ix_articles_published_at")
    op.execute("DROP INDEX IF EXISTS ix_articles_source")
    op.execute("DROP INDEX IF EXISTS ix_article_chunks_search_vector")
    op.execute("ALTER TABLE article_chunks DROP COLUMN IF EXISTS search_vector")
