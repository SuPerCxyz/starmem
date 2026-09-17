"""Add P1 attachment and native ingestion persistence."""

from alembic import op

revision = "0007_p1_ingestion"
down_revision = "0006_user_metadata_overrides"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS attachments (
            id UUID PRIMARY KEY,
            entry_id UUID NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
            storage_key VARCHAR(255) NOT NULL UNIQUE,
            original_filename TEXT NOT NULL,
            media_type VARCHAR(255) NOT NULL,
            size_bytes BIGINT NOT NULL,
            content_hash VARCHAR(64) NOT NULL,
            processing_status VARCHAR(32) NOT NULL DEFAULT 'pending',
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_attachment_entry_hash UNIQUE (entry_id, content_hash)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_attachments_entry_created "
        "ON attachments (entry_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_attachments_content_hash ON attachments (content_hash)"
    )
    op.execute(
        "ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS "
        "entry_id UUID REFERENCES entries(id) ON DELETE CASCADE"
    )
    op.execute(
        "ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS "
        "attachment_id UUID REFERENCES attachments(id) ON DELETE SET NULL"
    )
    op.execute(
        "ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS "
        "input_kind VARCHAR(32) NOT NULL DEFAULT 'external_sync'"
    )
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS phase VARCHAR(64)")
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(255)")
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS original_name TEXT")
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS media_type VARCHAR(255)")
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS source_uri TEXT")
    op.execute(
        "ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS "
        "metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb"
    )
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS error_code VARCHAR(64)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_ingestion_jobs_idempotency "
        "ON ingestion_jobs (idempotency_key) WHERE idempotency_key IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ingestion_jobs_entry_created "
        "ON ingestion_jobs (entry_id, created_at)"
    )
    op.execute(
        "ALTER TABLE content_units ADD COLUMN IF NOT EXISTS "
        "attachment_id UUID REFERENCES attachments(id) ON DELETE SET NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_content_units_attachment ON content_units (attachment_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_content_units_attachment")
    op.execute("ALTER TABLE content_units DROP COLUMN IF EXISTS attachment_id")
    op.execute("DROP INDEX IF EXISTS ix_ingestion_jobs_entry_created")
    op.execute("DROP INDEX IF EXISTS ix_ingestion_jobs_idempotency")
    for column in (
        "error_code",
        "metadata_json",
        "source_uri",
        "media_type",
        "original_name",
        "idempotency_key",
        "phase",
        "input_kind",
        "attachment_id",
        "entry_id",
    ):
        op.execute(f"ALTER TABLE ingestion_jobs DROP COLUMN IF EXISTS {column}")
    op.execute("DROP TABLE IF EXISTS attachments")
