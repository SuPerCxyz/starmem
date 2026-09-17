from __future__ import annotations

import base64
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from app.models import AIJob, ContentUnit, Entry, EntryVersion, Source
from app.schemas import EntryCreate, EntryUpdate
from app.services.safety import scan_entry

JOB_TYPES = (
    "chunk",
    "embedding",
    "classify",
    "summarize",
    "tag",
    "entity_extract",
    "time_extract",
    "project_classify",
    "topic_classify",
    "memory_extract",
    "relation_build",
    "image_describe",
)


def get_native_source(db: Session) -> Source:
    source = db.scalar(select(Source).where(Source.is_native.is_(True)))
    if source:
        return source
    source = Source(
        name="StarMem Native",
        source_type="native",
        description="Content captured directly in StarMem.",
        is_native=True,
    )
    db.add(source)
    db.flush()
    return source


def _next_version_number(db: Session, entry_id: UUID) -> int:
    latest = db.scalar(
        select(func.max(EntryVersion.version_number)).where(EntryVersion.entry_id == entry_id)
    )
    return (latest or 0) + 1


def _create_jobs(db: Session, entry: Entry) -> None:
    for job_type in JOB_TYPES:
        db.add(AIJob(entry_id=entry.id, job_type=job_type, generation=entry.ai_generation))


def _enqueue(entry_id: UUID) -> str | None:
    try:
        from app.worker import process_entry

        process_entry.send(str(entry_id))
        return None
    except Exception:
        return "Queue unavailable; entry can be reprocessed later."


def create_entry(db: Session, payload: EntryCreate) -> Entry:
    source = get_native_source(db)
    entry = Entry(source_id=source.id, **payload.model_dump())
    db.add(entry)
    db.flush()
    db.add(
        EntryVersion(
            entry_id=entry.id,
            version_number=1,
            raw_content=entry.raw_content,
            title=entry.title,
            change_source="user",
        )
    )
    db.add(
        ContentUnit(
            owner_type="entry",
            owner_id=entry.id,
            source_id=source.id,
            entry_id=entry.id,
            unit_type="entry",
            sequence=0,
            content=entry.raw_content,
            event_time=entry.event_time_start,
        )
    )
    _create_jobs(db, entry)
    scan_entry(db, entry)
    db.commit()
    db.refresh(entry)

    queue_error = _enqueue(entry.id)
    if queue_error:
        entry.ai_status = "retrying"
        for job in db.scalars(select(AIJob).where(AIJob.entry_id == entry.id)).all():
            job.status = "retrying"
            job.error = queue_error
        db.commit()
        db.refresh(entry)
    return entry


def get_entry(db: Session, entry_id: UUID, include_deleted: bool = False) -> Entry | None:
    statement = select(Entry).where(Entry.id == entry_id)
    if not include_deleted:
        statement = statement.where(Entry.deleted_at.is_(None))
    return db.scalar(statement)


def update_entry(
    db: Session, entry: Entry, payload: EntryUpdate, change_source: str = "user"
) -> Entry:
    changes = payload.model_dump(exclude_unset=True)
    raw_changed = "raw_content" in changes and changes["raw_content"] != entry.raw_content
    for field, value in changes.items():
        setattr(entry, field, value)
    if raw_changed:
        content_unit = db.scalar(
            select(ContentUnit).where(
                ContentUnit.entry_id == entry.id, ContentUnit.owner_type == "entry"
            )
        )
        if content_unit:
            content_unit.content = entry.raw_content
            content_unit.event_time = entry.event_time_start
        db.add(
            EntryVersion(
                entry_id=entry.id,
                version_number=_next_version_number(db, entry.id),
                raw_content=entry.raw_content,
                title=entry.title,
                change_source=change_source,
            )
        )
        entry.ai_generation += 1
        entry.ai_status = "pending"
        _create_jobs(db, entry)
        scan_entry(db, entry)
    db.commit()
    db.refresh(entry)
    if raw_changed:
        queue_error = _enqueue(entry.id)
        if queue_error:
            entry.ai_status = "retrying"
            db.commit()
            db.refresh(entry)
    return entry


def reprocess_entry(db: Session, entry: Entry) -> Entry:
    entry.ai_generation += 1
    entry.ai_status = "pending"
    _create_jobs(db, entry)
    db.commit()
    db.refresh(entry)
    queue_error = _enqueue(entry.id)
    if queue_error:
        entry.ai_status = "retrying"
        db.commit()
        db.refresh(entry)
    return entry


def soft_delete_entry(db: Session, entry: Entry, deleted_at: datetime) -> None:
    entry.deleted_at = deleted_at
    db.commit()


def encode_cursor(entry: Entry) -> str:
    raw = f"{entry.created_at.isoformat()}|{entry.id}".encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor: str) -> tuple[datetime, UUID] | None:
    try:
        created_at, entry_id = (
            base64.urlsafe_b64decode(cursor.encode()).decode().split("|", maxsplit=1)
        )
        return datetime.fromisoformat(created_at), UUID(entry_id)
    except (ValueError, UnicodeDecodeError):
        return None


def list_entries(
    db: Session,
    *,
    cursor: str | None = None,
    limit: int = 30,
    start: datetime | None = None,
    end: datetime | None = None,
    pinned: bool | None = None,
    favorite: bool | None = None,
) -> tuple[list[Entry], str | None]:
    statement = select(Entry).where(Entry.deleted_at.is_(None))
    if start:
        statement = statement.where(Entry.created_at >= start)
    if end:
        statement = statement.where(Entry.created_at <= end)
    if pinned is not None:
        statement = statement.where(Entry.is_pinned == pinned)
    if favorite is not None:
        statement = statement.where(Entry.is_favorite == favorite)
    if cursor and (decoded := decode_cursor(cursor)):
        created_at, entry_id = decoded
        statement = statement.where(
            or_(
                Entry.created_at < created_at,
                and_(Entry.created_at == created_at, Entry.id < entry_id),
            )
        )
    entries = db.scalars(
        statement.order_by(desc(Entry.created_at), desc(Entry.id)).limit(limit + 1)
    ).all()
    next_cursor = encode_cursor(entries[-2]) if len(entries) > limit else None
    return entries[:limit], next_cursor
