"""Add P1 knowledge workbench persistence."""

from alembic import op

revision = "0008_p1_workbench"
down_revision = "0007_p1_ingestion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS saved_searches (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            query TEXT NOT NULL,
            source_scope VARCHAR(32) NOT NULL DEFAULT 'all',
            filters_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_saved_search_user_name UNIQUE (user_id, name)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_saved_search_user_id ON saved_searches (user_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_saved_search_user_updated "
        "ON saved_searches (user_id, updated_at)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS entry_safety_scans (
            id UUID PRIMARY KEY,
            entry_id UUID NOT NULL UNIQUE REFERENCES entries(id) ON DELETE CASCADE,
            detected BOOLEAN NOT NULL DEFAULT FALSE,
            findings_json JSONB NOT NULL DEFAULT '[]'::jsonb,
            content_hash VARCHAR(64) NOT NULL,
            scanner_version VARCHAR(64) NOT NULL DEFAULT 'local-v1',
            scanned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entry_safety_scans_detected ON entry_safety_scans (detected)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entry_safety_scans_hash ON entry_safety_scans (content_hash)"
    )
    op.execute(
        "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS "
        "model_routing JSONB NOT NULL DEFAULT '{}'::jsonb"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE user_settings DROP COLUMN IF EXISTS model_routing")
    op.execute("DROP INDEX IF EXISTS ix_entry_safety_scans_hash")
    op.execute("DROP INDEX IF EXISTS ix_entry_safety_scans_detected")
    op.execute("DROP TABLE IF EXISTS entry_safety_scans")
    op.execute("DROP INDEX IF EXISTS ix_saved_search_user_updated")
    op.execute("DROP INDEX IF EXISTS ix_saved_search_user_id")
    op.execute("DROP TABLE IF EXISTS saved_searches")
