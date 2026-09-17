"""Small hook for consolidating Memories into Knowledge without replacing facts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AiDerivationMeta, Knowledge, Memory


def memory_context(db: Session, memory_ids: list[UUID]) -> list[Memory]:
    if not memory_ids:
        return []
    return db.scalars(
        select(Memory).where(Memory.id.in_(memory_ids), Memory.status == "active")
    ).all()


def create_knowledge(
    db: Session,
    *,
    title: str,
    content: str,
    memory_ids: list[UUID],
    provider: str | None = None,
    model: str | None = None,
    prompt_name: str | None = None,
    prompt_version: int | None = None,
    schema_version: str | None = None,
    prompt_hash: str | None = None,
) -> Knowledge:
    """Create a derived Knowledge document while retaining Atomic Memories."""
    if not memory_context(db, memory_ids):
        raise ValueError("Knowledge requires at least one active Memory")
    knowledge = Knowledge(
        title=title,
        content=content,
        status="derived",
        metadata_json={"memory_ids": [str(memory_id) for memory_id in memory_ids]},
    )
    db.add(knowledge)
    db.flush()
    if provider:
        db.add(
            AiDerivationMeta(
                object_type="knowledge",
                object_id=knowledge.id,
                provider=provider,
                model=model,
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                schema_version=schema_version,
                prompt_hash=prompt_hash,
            )
        )
    db.commit()
    return knowledge
