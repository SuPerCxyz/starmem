"""Read relations that were produced by relation_build jobs."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Entry, Relation
from app.schemas import RelationOut, RelationTargetOut


def _entry_target(db: Session, entry_id: UUID) -> Entry | None:
    return db.scalar(select(Entry).where(Entry.id == entry_id, Entry.deleted_at.is_(None)))


def list_relations(db: Session, entry_id: UUID, *, limit: int = 50) -> list[RelationOut]:
    rows = db.scalars(
        select(Relation)
        .where(
            or_(
                (Relation.source_type == "entry") & (Relation.source_id == entry_id),
                (Relation.target_type == "entry") & (Relation.target_id == entry_id),
            )
        )
        .order_by(Relation.created_at.desc())
        .limit(limit)
    ).all()
    results: list[RelationOut] = []
    for relation in rows:
        outbound = relation.source_type == "entry" and relation.source_id == entry_id
        other_type = relation.target_type if outbound else relation.source_type
        other_id = relation.target_id if outbound else relation.source_id
        target = _entry_target(db, other_id) if other_type == "entry" else None
        results.append(
            RelationOut(
                id=relation.id,
                relation_type=relation.relation_type,
                direction="outbound" if outbound else "inbound",
                source_type=relation.source_type,
                source_id=relation.source_id,
                target_type=relation.target_type,
                target_id=relation.target_id,
                confidence=relation.confidence,
                source=relation.source,
                created_at=relation.created_at,
                target=(
                    RelationTargetOut(
                        id=target.id,
                        title=target.title,
                        snippet=target.raw_content.replace("\n", " ")[:200],
                        created_at=target.created_at,
                    )
                    if target
                    else None
                ),
            )
        )
    return results
