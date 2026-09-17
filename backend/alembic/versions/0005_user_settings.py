"""Add single-user settings for global AI instructions and search scope."""

from alembic import op

revision = "0005_user_settings"
down_revision = "0004_memory_candidates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            global_ai_instructions TEXT,
            default_source_scope VARCHAR(32) NOT NULL DEFAULT 'all',
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_settings")
