"""Add gap-closure persistence: ask analytics, curation status and prompt schema overrides."""

from alembic import op

revision = "0009_p1_gap_closure"
down_revision = "0008_p1_workbench"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ask_queries (
            id UUID PRIMARY KEY,
            query_text TEXT NOT NULL,
            source_scope VARCHAR(32) NOT NULL DEFAULT 'all',
            result_count INTEGER NOT NULL DEFAULT 0,
            latency_ms INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_ask_queries_created ON ask_queries (created_at)")
    op.execute(
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS metadata_json "
        "JSONB NOT NULL DEFAULT '{}'::jsonb"
    )
    op.execute(
        "ALTER TABLE topics ADD COLUMN IF NOT EXISTS metadata_json "
        "JSONB NOT NULL DEFAULT '{}'::jsonb"
    )
    op.execute(
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'active'"
    )
    op.execute(
        "ALTER TABLE topics ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'active'"
    )
    op.execute(
        "ALTER TABLE entities ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'active'"
    )
    op.execute("ALTER TABLE prompt_versions ADD COLUMN IF NOT EXISTS schema_json JSONB")


def downgrade() -> None:
    op.execute("ALTER TABLE prompt_versions DROP COLUMN IF EXISTS schema_json")
    op.execute("ALTER TABLE entities DROP COLUMN IF EXISTS status")
    op.execute("ALTER TABLE topics DROP COLUMN IF EXISTS status")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS status")
    op.execute("ALTER TABLE topics DROP COLUMN IF EXISTS metadata_json")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS metadata_json")
    op.execute("DROP INDEX IF EXISTS ix_ask_queries_created")
    op.execute("DROP TABLE IF EXISTS ask_queries")
