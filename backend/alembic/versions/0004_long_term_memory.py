"""long-term memory system — user_memories table + enhanced investor_personas

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-01
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE user_memories (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category VARCHAR(30) NOT NULL,
            content TEXT NOT NULL,
            embedding vector(1536),
            confidence FLOAT NOT NULL DEFAULT 0.8,
            source VARCHAR(20) NOT NULL DEFAULT 'inferred',
            active BOOLEAN NOT NULL DEFAULT true,
            accessed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("CREATE INDEX ix_user_memories_user_id ON user_memories (user_id)")
    op.execute("CREATE INDEX ix_user_memories_category ON user_memories (category)")
    op.execute(
        "CREATE INDEX ix_user_memories_active "
        "ON user_memories (user_id, active) WHERE active = true"
    )
    op.execute("""
        CREATE INDEX ix_user_memories_embedding
        ON user_memories USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    op.execute(
        "ALTER TABLE investor_personas ADD COLUMN IF NOT EXISTS investment_style VARCHAR(30)"
    )
    op.execute("ALTER TABLE investor_personas ADD COLUMN IF NOT EXISTS investment_goals TEXT")
    op.execute(
        "ALTER TABLE investor_personas ADD COLUMN IF NOT EXISTS preferred_tickers VARCHAR(20)[]"
    )
    op.execute(
        "ALTER TABLE investor_personas ADD COLUMN IF NOT EXISTS avoided_tickers VARCHAR(20)[]"
    )
    op.execute(
        "ALTER TABLE investor_personas ADD COLUMN IF NOT EXISTS sector_preferences VARCHAR(50)[]"
    )
    op.execute(
        "ALTER TABLE investor_personas ADD COLUMN IF NOT EXISTS avoided_sectors VARCHAR(50)[]"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE investor_personas DROP COLUMN IF EXISTS avoided_sectors")
    op.execute("ALTER TABLE investor_personas DROP COLUMN IF EXISTS sector_preferences")
    op.execute("ALTER TABLE investor_personas DROP COLUMN IF EXISTS avoided_tickers")
    op.execute("ALTER TABLE investor_personas DROP COLUMN IF EXISTS preferred_tickers")
    op.execute("ALTER TABLE investor_personas DROP COLUMN IF EXISTS investment_goals")
    op.execute("ALTER TABLE investor_personas DROP COLUMN IF EXISTS investment_style")
    op.execute("DROP TABLE IF EXISTS user_memories")
