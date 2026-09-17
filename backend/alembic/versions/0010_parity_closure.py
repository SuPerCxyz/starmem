"""Add multi-classification and parity-closure persistence."""

from alembic import op

revision = "0010_parity_closure"
down_revision = "0009_p1_gap_closure"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE entries ADD COLUMN IF NOT EXISTS content_types "
        "JSONB NOT NULL DEFAULT '[]'::jsonb"
    )
    op.execute("ALTER TABLE memories ADD COLUMN IF NOT EXISTS expired_at TIMESTAMPTZ")


def downgrade() -> None:
    op.execute("ALTER TABLE memories DROP COLUMN IF EXISTS expired_at")
    op.execute("ALTER TABLE entries DROP COLUMN IF EXISTS content_types")
