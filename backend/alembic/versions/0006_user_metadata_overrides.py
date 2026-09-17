"""Add explicit user removal state for AI tag suggestions."""

from alembic import op

revision = "0006_user_metadata_overrides"
down_revision = "0005_user_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE entry_tags ADD COLUMN IF NOT EXISTS "
        "user_removed BOOLEAN NOT NULL DEFAULT FALSE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE entry_tags DROP COLUMN IF EXISTS user_removed")
