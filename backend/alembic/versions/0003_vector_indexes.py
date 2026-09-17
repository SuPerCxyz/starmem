"""Add pgvector indexes for retrieval collections."""

from alembic import op

revision = "0003_vector_indexes"
down_revision = "0002_content_unit_fts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entry_chunks_embedding "
        "ON entry_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_memories_embedding "
        "ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_memories_embedding")
    op.execute("DROP INDEX IF EXISTS ix_entry_chunks_embedding")
