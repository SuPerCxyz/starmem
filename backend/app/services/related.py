"""Deterministic related-entry signals layered on top of similarity search."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Entity, Entry, EntryEntity, EntryTag, Observation, Tag
from app.schemas import RelatedEntryOut
from app.services.workbench import similar_entries

ERROR_HINTS = ("error", "exception", "故障", "报错", "失败")


def _tag_names(db: Session, entry_id: UUID) -> set[str]:
    return {
        name.casefold()
        for name in db.scalars(
            select(Tag.normalized_name)
            .join(EntryTag, EntryTag.tag_id == Tag.id)
            .where(EntryTag.entry_id == entry_id, EntryTag.user_removed.is_(False))
        ).all()
    }


def _entities(db: Session, entry_id: UUID) -> dict[str, str]:
    rows = db.execute(
        select(Entity.normalized_name, Entity.entity_type)
        .join(EntryEntity, EntryEntity.entity_id == Entity.id)
        .where(EntryEntity.entry_id == entry_id)
    ).all()
    return {name.casefold(): entity_type for name, entity_type in rows}


def _observation_name(db: Session, entry_id: UUID, observation_type: str) -> str | None:
    observation = db.scalar(
        select(Observation).where(
            Observation.entry_id == entry_id,
            Observation.observation_type == observation_type,
        )
    )
    if not observation:
        return None
    value = (observation.data_json or {}).get("name")
    return str(value).casefold() if value else None


def _has_error_signal(entry: Entry) -> bool:
    lowered = entry.raw_content.casefold()
    return any(hint in lowered for hint in ERROR_HINTS)


def related_entries(
    db: Session,
    entry_id: UUID,
    *,
    source_scope: str = "all",
    limit: int = 5,
) -> list[RelatedEntryOut]:
    entry = db.get(Entry, entry_id)
    if not entry or entry.deleted_at is not None:
        raise ValueError("Entry not found")

    own_tags = _tag_names(db, entry_id)
    own_entities = _entities(db, entry_id)
    own_hosts = {name for name, kind in own_entities.items() if kind == "host"}
    own_project = _observation_name(db, entry_id, "project")
    own_topic = _observation_name(db, entry_id, "topic")
    own_error = _has_error_signal(entry)

    candidates: dict[UUID, dict[str, object]] = {}

    def add(candidate_id: UUID, *, score: float, reason: str) -> None:
        bucket = candidates.setdefault(candidate_id, {"score": 0.0, "reasons": []})
        bucket["score"] = round(float(bucket["score"]) + score, 5)
        reasons = bucket["reasons"]
        if reason not in reasons:
            reasons.append(reason)

    for candidate in similar_entries(db, entry_id, source_scope=source_scope, limit=limit * 3):
        if candidate.score >= 0.2:
            add(candidate.entry_id, score=candidate.score, reason="语义相似度")

    shared_tag_rows = (
        db.execute(
            select(EntryTag.entry_id)
            .join(Tag, Tag.id == EntryTag.tag_id)
            .where(
                Tag.normalized_name.in_(sorted(own_tags)),
                EntryTag.entry_id != entry_id,
                EntryTag.user_removed.is_(False),
            )
        ).all()
        if own_tags
        else []
    )
    for (candidate_id,) in shared_tag_rows:
        add(candidate_id, score=0.3, reason="共享标签")

    if own_entities:
        entity_ids = db.scalars(
            select(Entity.id).where(Entity.normalized_name.in_(sorted(own_entities)))
        ).all()
        if entity_ids:
            shared_entity_rows = db.execute(
                select(EntryEntity.entry_id).where(
                    EntryEntity.entity_id.in_(entity_ids),
                    EntryEntity.entry_id != entry_id,
                )
            ).all()
            for (candidate_id,) in shared_entity_rows:
                add(candidate_id, score=0.35, reason="共享实体")

    if own_hosts:
        host_entities = db.scalars(
            select(Entity.id).where(Entity.normalized_name.in_(sorted(own_hosts)))
        ).all()
        if host_entities:
            for (candidate_id,) in db.execute(
                select(EntryEntity.entry_id).where(
                    EntryEntity.entity_id.in_(host_entities),
                    EntryEntity.entry_id != entry_id,
                )
            ).all():
                add(candidate_id, score=0.25, reason="同 Host")

    for observation_type, reason, weight in (
        ("project", "同 Project", 0.3),
        ("topic", "同 Topic", 0.25),
    ):
        own_name = own_project if observation_type == "project" else own_topic
        if not own_name:
            continue
        rows = db.scalars(
            select(Observation.entry_id).where(
                Observation.observation_type == observation_type,
                Observation.entry_id != entry_id,
            )
        ).all()
        for candidate_id in rows:
            other = _observation_name(db, candidate_id, observation_type)
            if other and other == own_name:
                add(candidate_id, score=weight, reason=reason)

    if own_error:
        error_candidates = db.scalars(
            select(Entry.id).where(
                Entry.id != entry_id,
                Entry.deleted_at.is_(None),
                Entry.raw_content.ilike("%error%"),
            )
        ).all()[: limit * 4]
        for candidate_id in error_candidates:
            candidate = db.get(Entry, candidate_id)
            if candidate and _has_error_signal(candidate):
                add(candidate_id, score=0.15, reason="同 Error")

    if not candidates:
        return []

    visible = {
        row.id: row
        for row in db.scalars(
            select(Entry).where(Entry.id.in_(list(candidates)), Entry.deleted_at.is_(None))
        ).all()
    }
    results = [
        RelatedEntryOut(
            entry_id=candidate_id,
            title=visible[candidate_id].title,
            score=round(min(1.0, float(data["score"])), 5),
            reasons=list(data["reasons"]),
            snippet=visible[candidate_id].raw_content.replace("\n", " ")[:260],
            created_at=visible[candidate_id].created_at,
        )
        for candidate_id, data in candidates.items()
        if candidate_id in visible
    ]
    results.sort(key=lambda item: item.score, reverse=True)
    return results[:limit]
