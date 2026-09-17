"""Bounded batch reprocessing and maintenance triggers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Entry, Source
from app.schemas import BatchReprocessInput, BatchReprocessOut
from app.services.entries import reprocess_entry

MAX_BATCH_ENTRIES = 200


def _filtered_entries(db: Session, payload: BatchReprocessInput) -> list[Entry]:
    statement = select(Entry).where(Entry.deleted_at.is_(None))
    if payload.source_scope == "native":
        statement = statement.join(Source, Source.id == Entry.source_id).where(
            Source.is_native.is_(True)
        )
    elif payload.source_scope == "external":
        statement = statement.join(Source, Source.id == Entry.source_id).where(
            Source.is_native.is_(False)
        )
    if payload.start:
        statement = statement.where(Entry.created_at >= payload.start)
    if payload.end:
        statement = statement.where(Entry.created_at <= payload.end)
    if payload.content_type:
        statement = statement.where(Entry.content_type == payload.content_type)
    return list(
        db.scalars(statement.order_by(Entry.created_at.desc()).limit(MAX_BATCH_ENTRIES + 1)).all()
    )


def reprocess_batch(db: Session, payload: BatchReprocessInput) -> BatchReprocessOut:
    if payload.source_scope not in {"all", "native", "external"}:
        raise ValueError("Unsupported source scope")
    if payload.entry_ids:
        if len(payload.entry_ids) > MAX_BATCH_ENTRIES:
            raise ValueError(f"Batch reprocess accepts at most {MAX_BATCH_ENTRIES} entries")
        entries = list(
            db.scalars(
                select(Entry).where(Entry.id.in_(payload.entry_ids), Entry.deleted_at.is_(None))
            ).all()
        )
        if len(entries) != len(set(payload.entry_ids)):
            raise ValueError("Some Entries do not exist or are deleted")
    else:
        entries = _filtered_entries(db, payload)
        if len(entries) > MAX_BATCH_ENTRIES:
            raise ValueError(
                f"Filter matches more than {MAX_BATCH_ENTRIES} entries; narrow the filter"
            )
        if not entries:
            raise ValueError("No entries match the filter")
    submitted: list[UUID] = []
    failed = 0
    for entry in entries:
        try:
            reprocess_entry(db, entry)
            submitted.append(entry.id)
        except Exception:
            db.rollback()
            failed += 1
    return BatchReprocessOut(
        submitted_count=len(submitted), failed_count=failed, entry_ids=submitted
    )


def rebuild_embeddings() -> str:
    """Queue a full-library embedding rebuild without touching raw Entries."""
    from app.db import SessionLocal
    from app.worker import process_entry

    queued = 0
    with SessionLocal() as db:
        entries = db.scalars(
            select(Entry).where(Entry.deleted_at.is_(None)).order_by(Entry.created_at)
        ).all()
        for entry in entries:
            try:
                process_entry.send(str(entry.id))
                queued += 1
            except Exception:
                break
    if queued == 0:
        raise RuntimeError("Queue unavailable; nothing was queued")
    return f"Queued embedding rebuild for {queued} entries"
