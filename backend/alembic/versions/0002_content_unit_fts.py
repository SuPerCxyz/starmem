"""Maintain ContentUnit full-text vectors.

Revision ID: 0002_content_unit_fts
Revises: 0001_initial_schema
Create Date: 2026-09-15
"""

from alembic import op

revision = "0002_content_unit_fts"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION starmem_content_unit_fts_update() RETURNS trigger AS $$
        BEGIN
          NEW.fts_vector := to_tsvector('simple', coalesce(NEW.content, ''));
          RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER starmem_content_unit_fts_trigger
        BEFORE INSERT OR UPDATE OF content ON content_units
        FOR EACH ROW EXECUTE FUNCTION starmem_content_unit_fts_update();
        """
    )
    op.execute("UPDATE content_units SET fts_vector = to_tsvector('simple', content)")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS starmem_content_unit_fts_trigger ON content_units")
    op.execute("DROP FUNCTION IF EXISTS starmem_content_unit_fts_update()")
