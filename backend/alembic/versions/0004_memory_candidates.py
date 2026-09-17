"""Add explicit Memory Candidate persistence."""

from alembic import op

revision = "0004_memory_candidates"
down_revision = "0003_vector_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_candidates (
            id UUID PRIMARY KEY,
            entry_id UUID NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
            observation_id UUID REFERENCES observations(id) ON DELETE SET NULL,
            source_chunk_id UUID REFERENCES entry_chunks(id) ON DELETE SET NULL,
            subject_type VARCHAR(64) NOT NULL DEFAULT 'entity',
            subject_key VARCHAR(255) NOT NULL,
            predicate VARCHAR(255) NOT NULL,
            scope_key VARCHAR(512) NOT NULL,
            value_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            value_key VARCHAR(512) NOT NULL,
            memory_text TEXT NOT NULL,
            salience VARCHAR(32) NOT NULL DEFAULT 'durable',
            durable BOOLEAN NOT NULL DEFAULT TRUE,
            confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            generation INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_memory_candidates_scope "
        "ON memory_candidates (scope_key, status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_memory_candidates_entry_generation "
        "ON memory_candidates (entry_id, generation)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS memory_candidates")
