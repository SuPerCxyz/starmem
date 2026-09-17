"""User curation of derived metadata: Entry metadata, Project/Topic/Entity management."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AIJob,
    Entity,
    Entry,
    EntryEntity,
    EntryTag,
    Observation,
    Project,
    Tag,
    Topic,
)
from app.schemas import (
    EntryAIStatusItemOut,
    EntryAIStatusOut,
    EntryMetadataInput,
    EntryMetadataOut,
)

USER_LOCKABLE_OBSERVATIONS = {
    "summary": "summary",
    "project": "project",
    "topic": "topic",
}

AI_STATUS_JOB_ORDER = (
    ("chunk", "索引"),
    ("embedding", "Embedding"),
    ("classify", "分类"),
    ("summarize", "摘要"),
    ("tag", "标签"),
    ("entity_extract", "实体"),
    ("time_extract", "时间"),
    ("project_classify", "项目"),
    ("topic_classify", "主题"),
    ("memory_extract", "Memory"),
    ("relation_build", "关系"),
    ("image_describe", "图片描述"),
)


def _user_observation(db: Session, entry: Entry, observation_type: str) -> Observation | None:
    return db.scalar(
        select(Observation).where(
            Observation.entry_id == entry.id,
            Observation.observation_type == observation_type,
            Observation.is_user_locked.is_(True),
        )
    )


def _upsert_user_observation(
    db: Session, entry: Entry, observation_type: str, data: dict[str, object]
) -> Observation:
    observation = _user_observation(db, entry, observation_type)
    if observation is None:
        observation = Observation(
            entry_id=entry.id,
            observation_type=observation_type,
            data_json={},
            source="user",
            is_user_locked=True,
            generation=entry.ai_generation,
        )
        db.add(observation)
        db.flush()
    observation.data_json = data
    observation.source = "user"
    observation.is_user_locked = True
    observation.generation = entry.ai_generation
    return observation


def visible_content_types(entry: Entry) -> list[str]:
    """Multi-classification with fallback to the single legacy primary type."""
    values = [str(value).strip() for value in (entry.content_types or []) if str(value).strip()]
    primary = (entry.content_type or "").strip()
    if primary and primary not in values:
        values.insert(0, primary)
    return list(dict.fromkeys(values))


def entry_metadata(db: Session, entry: Entry) -> EntryMetadataOut:
    summary = _user_observation(db, entry, "summary")
    types_locked = _user_observation(db, entry, "classification")
    project = _user_observation(db, entry, "project")
    topic = _user_observation(db, entry, "topic")
    description = db.scalar(
        select(Observation)
        .where(
            Observation.entry_id == entry.id,
            Observation.observation_type == "image_description",
        )
        .order_by(Observation.generation.desc())
        .limit(1)
    )
    description_job = db.scalar(
        select(AIJob)
        .where(AIJob.entry_id == entry.id, AIJob.job_type == "image_describe")
        .order_by(AIJob.generation.desc())
        .limit(1)
    )
    return EntryMetadataOut(
        entry_id=entry.id,
        content_type=entry.content_type,
        content_types=visible_content_types(entry),
        content_types_locked=types_locked is not None,
        importance=entry.importance,
        summary=(summary.data_json or {}).get("summary") if summary else None,
        summary_locked=summary is not None,
        project=(project.data_json or {}).get("name") if project else None,
        project_locked=project is not None,
        topic=(topic.data_json or {}).get("name") if topic else None,
        topic_locked=topic is not None,
        image_description=(description.data_json or {}).get("description") if description else None,
        image_description_status=description_job.status if description_job else None,
        image_description_detail=description_job.error if description_job else None,
    )


def update_entry_metadata(
    db: Session, entry: Entry, payload: EntryMetadataInput
) -> EntryMetadataOut:
    fields = payload.model_fields_set
    if "content_types" in fields and payload.content_types is not None:
        cleaned = [value.strip() for value in payload.content_types if value.strip()]
        if not cleaned:
            raise ValueError("content_types cannot be empty")
        entry.content_types = list(dict.fromkeys(cleaned))[:16]
        entry.content_type = entry.content_types[0]
        _upsert_user_observation(
            db,
            entry,
            "classification",
            {
                "content_type": entry.content_type,
                "content_types": entry.content_types,
                "confidence": 1.0,
                "reason": "user-curated",
                "is_inference": False,
            },
        )
    elif "content_type" in fields and payload.content_type:
        entry.content_type = payload.content_type.strip()
        if not entry.content_types:
            entry.content_types = [entry.content_type]
    if "importance" in fields and payload.importance is not None:
        entry.importance = payload.importance
    if "summary" in fields:
        if payload.summary is None:
            observation = _user_observation(db, entry, "summary")
            if observation:
                db.delete(observation)
        else:
            text = payload.summary.strip()
            if not text:
                raise ValueError("Summary cannot be blank")
            _upsert_user_observation(
                db,
                entry,
                "summary",
                {"summary": text, "confidence": 1.0, "is_inference": False},
            )
    for field, observation_type in (("project", "project"), ("topic", "topic")):
        if field not in fields:
            continue
        value = getattr(payload, field)
        if value is None:
            observation = _user_observation(db, entry, observation_type)
            if observation:
                db.delete(observation)
            continue
        name = " ".join(value.strip().split())
        if not name:
            raise ValueError(f"{field} cannot be blank")
        model = Project if observation_type == "project" else Topic
        item = db.scalar(select(model).where(model.name == name))
        if item is None:
            raise ValueError(f"{field.title()} not found; create or rename it in Workbench first")
        if item.status in {"merged", "deleted"}:
            raise ValueError(f"{field.title()} is not active")
        if item.status == "excluded":
            item.status = "active"
            item.source = "user"
            item.metadata_json = {
                **(item.metadata_json or {}),
                "restored_at": datetime.now(UTC).isoformat(),
            }
        _upsert_user_observation(
            db,
            entry,
            observation_type,
            {"name": item.name, "confidence": 1.0, "user_confirmed": True},
        )
    db.commit()
    db.refresh(entry)
    return entry_metadata(db, entry)


def entry_signal_map(db: Session, entry_ids: list[UUID]) -> dict[UUID, dict[str, object]]:
    """Batch tags and latest-per-step AI jobs for Entry card rendering."""
    signals: dict[UUID, dict[str, object]] = {}
    if not entry_ids:
        return signals
    for entry_id, name in db.execute(
        select(EntryTag.entry_id, Tag.name)
        .join(Tag, Tag.id == EntryTag.tag_id)
        .where(EntryTag.entry_id.in_(entry_ids), EntryTag.user_removed.is_(False))
        .order_by(Tag.name)
    ).all():
        signals.setdefault(entry_id, {}).setdefault("tags", []).append(name)
    latest: dict[tuple[UUID, str], AIJob] = {}
    for job in db.scalars(
        select(AIJob)
        .where(AIJob.entry_id.in_(entry_ids))
        .order_by(AIJob.generation.desc(), AIJob.created_at.desc())
    ).all():
        latest.setdefault((job.entry_id, job.job_type), job)
    for (entry_id, job_type), job in latest.items():
        signals.setdefault(entry_id, {}).setdefault("jobs", {})[job_type] = job
    return signals


def entry_ai_status_items(jobs: dict[str, AIJob]) -> list[EntryAIStatusItemOut]:
    return [
        EntryAIStatusItemOut(
            job_id=jobs[job_type].id,
            job_type=job_type,
            label=label,
            status=jobs[job_type].status,
            error=jobs[job_type].error,
        )
        for job_type, label in AI_STATUS_JOB_ORDER
        if job_type in jobs
    ]


def entry_ai_status(db: Session, entry: Entry) -> EntryAIStatusOut:
    """Aggregate per-step AI job status for the Entry card."""
    jobs = db.scalars(
        select(AIJob)
        .where(AIJob.entry_id == entry.id)
        .order_by(AIJob.generation.desc(), AIJob.created_at.desc())
    ).all()
    latest: dict[str, AIJob] = {}
    for job in jobs:
        latest.setdefault(job.job_type, job)
    items = [
        EntryAIStatusItemOut(
            job_id=latest[job_type].id,
            job_type=job_type,
            label=label,
            status=latest[job_type].status,
            error=latest[job_type].error,
        )
        for job_type, label in AI_STATUS_JOB_ORDER
        if job_type in latest
    ]
    return EntryAIStatusOut(
        entry_id=entry.id,
        ai_status=entry.ai_status,
        generation=entry.ai_generation,
        items=items,
    )


def _observation_match_count(db: Session, observation_type: str, name: str) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(Observation)
            .where(
                Observation.observation_type == observation_type,
                Observation.data_json["name"].as_string() == name,
            )
        )
        or 0
    )


def _repoint_observations(
    db: Session, observation_type: str, source_name: str, target_name: str
) -> int:
    observations = db.scalars(
        select(Observation).where(
            Observation.observation_type == observation_type,
            Observation.data_json["name"].as_string() == source_name,
        )
    ).all()
    for observation in observations:
        observation.data_json = {
            **(observation.data_json or {}),
            "name": target_name,
            "merged_from": source_name,
        }
    return len(observations)


def rename_object(db: Session, kind: str, item_id: UUID, name: str) -> dict[str, object]:
    new_name = " ".join(name.strip().split())
    if not new_name:
        raise ValueError("Name cannot be blank")
    if kind == "project":
        item = db.get(Project, item_id)
        observation_type = "project"
    elif kind == "topic":
        item = db.get(Topic, item_id)
        observation_type = "topic"
    else:
        entity = db.get(Entity, item_id)
        if not entity:
            raise LookupError("Entity not found")
        duplicate = db.scalar(
            select(Entity).where(
                Entity.entity_type == entity.entity_type,
                func.lower(Entity.canonical_name) == new_name.casefold(),
                Entity.id != entity.id,
            )
        )
        if duplicate:
            raise ValueError("Entity already exists")
        entity.canonical_name = new_name
        entity.normalized_name = new_name.casefold()
        entity.metadata_json = {
            **(entity.metadata_json or {}),
            "renamed_at": datetime.now(UTC).isoformat(),
        }
        db.commit()
        return {"id": str(entity.id), "name": entity.canonical_name, "kind": "entity"}
    if not item:
        raise LookupError(f"{kind.title()} not found")
    duplicate = db.scalar(
        select(type(item)).where(type(item).name == new_name, type(item).id != item.id)
    )
    if duplicate:
        raise ValueError(f"{kind.title()} already exists")
    old_name = item.name
    item.name = new_name
    item.source = "user"
    item.metadata_json = {
        **(item.metadata_json or {}),
        "renamed_at": datetime.now(UTC).isoformat(),
        "previous_name": old_name,
    }
    _repoint_observations(db, observation_type, old_name, new_name)
    db.commit()
    return {"id": str(item.id), "name": item.name, "kind": kind}


def set_object_status(db: Session, kind: str, item_id: UUID, status: str) -> dict[str, object]:
    if status not in {"active", "excluded"}:
        raise ValueError("Unsupported status")
    model = {"project": Project, "topic": Topic, "entity": Entity}.get(kind)
    if model is None:
        raise ValueError("Unsupported object kind")
    item = db.get(model, item_id)
    if not item:
        raise LookupError(f"{kind.title()} not found")
    if getattr(item, "status", None) in {"merged", "deleted"}:
        raise ValueError(f"{kind.title()} is not active")
    item.status = status
    item.metadata_json = {
        **(item.metadata_json or {}),
        "status_changed_at": datetime.now(UTC).isoformat(),
    }
    db.commit()
    return {"id": str(item.id), "kind": kind, "status": item.status}


def merge_object(db: Session, kind: str, source_id: UUID, target_id: UUID) -> dict[str, object]:
    if source_id == target_id:
        raise ValueError("Cannot merge an object into itself")
    if kind not in {"project", "topic"}:
        raise ValueError("Only Project and Topic merge is supported")
    model = Project if kind == "project" else Topic
    source = db.get(model, source_id)
    target = db.get(model, target_id)
    if not source or not target:
        raise LookupError(f"{kind.title()} not found")
    if source.status in {"merged", "excluded"}:
        raise ValueError(f"{kind.title()} is not active")
    moved = _repoint_observations(db, kind, source.name, target.name)
    source.status = "merged"
    source.metadata_json = {
        **(source.metadata_json or {}),
        "merged_into": str(target.id),
        "merged_into_name": target.name,
        "merged_at": datetime.now(UTC).isoformat(),
        "moved_observations": moved,
    }
    target.source = "user"
    db.commit()
    return {
        "source_id": str(source.id),
        "target_id": str(target.id),
        "kind": kind,
        "moved_observations": moved,
    }


def merge_entity(db: Session, source_id: UUID, target_id: UUID) -> dict[str, object]:
    if source_id == target_id:
        raise ValueError("Cannot merge an entity into itself")
    source = db.get(Entity, source_id)
    target = db.get(Entity, target_id)
    if not source or not target:
        raise LookupError("Entity not found")
    if source.entity_type != target.entity_type:
        raise ValueError("Entities must share the same type")
    links = db.scalars(select(EntryEntity).where(EntryEntity.entity_id == source.id)).all()
    moved = 0
    for link in links:
        existing = db.get(EntryEntity, (link.entry_id, target.id))
        entry_id = link.entry_id
        mention = link.mention_text
        confidence = link.confidence
        link_source = link.source
        db.delete(link)
        if existing:
            continue
        db.add(
            EntryEntity(
                entry_id=entry_id,
                entity_id=target.id,
                mention_text=mention,
                confidence=confidence,
                source=link_source,
            )
        )
        moved += 1
    observation_count = 0
    for observation in db.scalars(
        select(Observation).where(Observation.observation_type == "entities")
    ).all():
        entities = (observation.data_json or {}).get("entities")
        if not isinstance(entities, list):
            continue
        changed = False
        for item in entities:
            if isinstance(item, dict) and item.get("name") == source.canonical_name:
                item["name"] = target.canonical_name
                changed = True
        if changed:
            observation.data_json = {**(observation.data_json or {}), "entities": entities}
            observation_count += 1
    source.status = "merged"
    source.metadata_json = {
        **(source.metadata_json or {}),
        "merged_into": str(target.id),
        "merged_at": datetime.now(UTC).isoformat(),
        "moved_links": moved,
        "moved_observations": observation_count,
    }
    db.commit()
    return {
        "source_id": str(source.id),
        "target_id": str(target.id),
        "kind": "entity",
        "moved_links": moved,
        "moved_observations": observation_count,
    }
