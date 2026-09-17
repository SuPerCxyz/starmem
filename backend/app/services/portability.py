"""Portable, secret-safe native import/export helpers."""

from __future__ import annotations

import io
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import desc, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import (
    Attachment,
    Entity,
    Entry,
    EntryEntity,
    EntryTag,
    Memory,
    MemorySource,
    Observation,
    Source,
    Tag,
)
from app.schemas import EntryCreate
from app.services.entries import create_entry
from app.storage import StorageError, read_attachment, verify_attachment

MAX_EXPORT_ENTRIES = 10_000
MAX_IMPORT_ENTRIES = 100
MAX_IMPORT_ERRORS = 32


@dataclass(frozen=True)
class ExportBundle:
    content: bytes
    media_type: str
    filename: str


@dataclass(frozen=True)
class ImportResult:
    created_count: int
    skipped_count: int
    entry_ids: list[str]
    errors: list[dict[str, object]]


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _entry_record(db: Session, entry: Entry) -> dict[str, object]:
    tags = db.execute(
        select(Tag.name)
        .join(EntryTag, EntryTag.tag_id == Tag.id)
        .where(EntryTag.entry_id == entry.id, EntryTag.user_removed.is_(False))
        .order_by(Tag.name)
    ).all()
    entities = (
        db.execute(
            select(Entity)
            .join(EntryEntity, EntryEntity.entity_id == Entity.id)
            .where(EntryEntity.entry_id == entry.id)
            .order_by(Entity.entity_type, Entity.canonical_name)
        )
        .scalars()
        .all()
    )
    observations = db.scalars(
        select(Observation).where(Observation.entry_id == entry.id).order_by(Observation.created_at)
    ).all()
    memories = db.scalars(
        select(Memory)
        .where(
            Memory.status.in_(("active", "conflicted")),
            or_(
                Memory.source_entry_id == entry.id,
                Memory.id.in_(
                    select(MemorySource.memory_id).where(MemorySource.entry_id == entry.id)
                ),
            ),
        )
        .order_by(desc(Memory.created_at))
    ).all()
    attachments = db.scalars(
        select(Attachment).where(Attachment.entry_id == entry.id).order_by(Attachment.created_at)
    ).all()
    return {
        "id": str(entry.id),
        "title": entry.title,
        "raw_content": entry.raw_content,
        "content_format": entry.content_format,
        "content_type": entry.content_type,
        "source_uri": entry.source_uri,
        "event_time_start": _iso(entry.event_time_start),
        "event_time_end": _iso(entry.event_time_end),
        "created_at": _iso(entry.created_at),
        "updated_at": _iso(entry.updated_at),
        "is_pinned": entry.is_pinned,
        "is_favorite": entry.is_favorite,
        "importance": entry.importance,
        "tags": [name for (name,) in tags],
        "entities": [
            {
                "id": str(entity.id),
                "name": entity.canonical_name,
                "entity_type": entity.entity_type,
                "normalized_name": entity.normalized_name,
            }
            for entity in entities
        ],
        "observations": [
            {
                "id": str(observation.id),
                "observation_type": observation.observation_type,
                "data_json": observation.data_json or {},
                "source": observation.source,
                "generation": observation.generation,
                "created_at": _iso(observation.created_at),
            }
            for observation in observations
        ],
        "memories": [
            {
                "id": str(memory.id),
                "status": memory.status,
                "subject_type": memory.subject_type,
                "subject_key": memory.subject_key,
                "predicate": memory.predicate,
                "scope_key": memory.scope_key,
                "value_json": memory.value_json or {},
                "value_key": memory.value_key,
                "memory_text": memory.memory_text,
                "salience": memory.salience,
                "durable": memory.durable,
                "confidence": memory.confidence,
            }
            for memory in memories
        ],
        "attachments": [
            {
                "id": str(attachment.id),
                "original_filename": attachment.original_filename,
                "media_type": attachment.media_type,
                "size_bytes": attachment.size_bytes,
                "content_hash": attachment.content_hash,
                "processing_status": attachment.processing_status,
                "metadata_json": attachment.metadata_json or {},
                "created_at": _iso(attachment.created_at),
            }
            for attachment in attachments
        ],
    }


def export_records(
    db: Session,
    *,
    source_scope: str = "all",
    include_deleted: bool = False,
) -> list[dict[str, object]]:
    statement = select(Entry).join(Source, Source.id == Entry.source_id)
    if not include_deleted:
        statement = statement.where(Entry.deleted_at.is_(None))
    if source_scope not in {"all", "native", "external"}:
        raise ValueError("Unsupported source scope")
    if source_scope != "all":
        statement = statement.where(Source.is_native == (source_scope == "native"))
    statement = statement.order_by(Entry.created_at, Entry.id).limit(MAX_EXPORT_ENTRIES)
    entries = db.scalars(statement).all()
    return [_entry_record(db, entry) for entry in entries]


def _safe_filename(filename: str) -> str:
    name = Path(filename or "attachment").name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return name[:120] or "attachment"


def _markdown(records: list[dict[str, object]]) -> bytes:
    sections: list[str] = []
    for record in records:
        title = str(record.get("title") or "未命名记录").replace("\n", " ")
        sections.append(
            f"<!-- starmem-entry-id: {record['id']} -->\n\n# {title}\n\n{record['raw_content']}"
        )
    return ("\n\n---\n\n".join(sections) + ("\n" if sections else "")).encode("utf-8")


def build_export(
    db: Session,
    *,
    export_format: str,
    source_scope: str = "all",
) -> ExportBundle:
    records = export_records(db, source_scope=source_scope)
    normalized = export_format.casefold()
    if normalized == "json":
        content = json.dumps(
            {"format": "starmem.native.v1", "entries": records},
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8")
        return ExportBundle(content, "application/json", "starmem-export.json")
    if normalized == "jsonl":
        content = "".join(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            for record in records
        ).encode("utf-8")
        return ExportBundle(content, "application/x-ndjson", "starmem-export.jsonl")
    if normalized == "markdown":
        return ExportBundle(_markdown(records), "text/markdown; charset=utf-8", "starmem-export.md")
    if normalized != "zip":
        raise ValueError("Unsupported export format")
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr(
            "starmem-export.json",
            json.dumps(
                {"format": "starmem.native.v1", "entries": records},
                ensure_ascii=False,
                indent=2,
            ),
        )
        for record in records:
            for attachment in record["attachments"]:
                attachment_id = str(attachment["id"])
                try:
                    attachment_row = db.get(Attachment, UUID(attachment_id))
                    if not attachment_row or not verify_attachment(
                        attachment_row.storage_key, str(attachment["content_hash"])
                    ):
                        continue
                    path = read_attachment(attachment_row.storage_key)
                    bundle.writestr(
                        f"attachments/{record['id']}/{attachment_id}-{_safe_filename(str(attachment['original_filename']))}",
                        path.read_bytes(),
                    )
                except (StorageError, OSError, ValueError, TypeError):
                    continue
    return ExportBundle(
        archive.getvalue(),
        "application/zip",
        f"starmem-export-{datetime.now().strftime('%Y%m%d')}.zip",
    )


def _parse_import_records(data: bytes, filename: str | None) -> list[dict[str, object]]:
    text = data.decode("utf-8-sig")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = [json.loads(line) for line in text.splitlines() if line.strip()]
    if isinstance(value, dict):
        if value.get("format") not in {None, "starmem.native.v1"}:
            raise ValueError("Unsupported import format")
        value = value.get("entries")
    if not isinstance(value, list):
        raise ValueError("Import must contain an entries array or JSONL records")
    if len(value) > MAX_IMPORT_ENTRIES:
        raise ValueError("Import exceeds the entry limit")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError("Each imported record must be an object")
    return value


def import_native_records(db: Session, data: bytes, *, filename: str | None = None) -> ImportResult:
    records = _parse_import_records(data, filename)
    created_ids: list[str] = []
    skipped = 0
    errors: list[dict[str, object]] = []
    for index, record in enumerate(records):
        try:
            raw_content = record.get("raw_content")
            if not isinstance(raw_content, str) or not raw_content.strip():
                raise ValueError("raw_content is required")
            title = record.get("title")
            if title is not None and not isinstance(title, str):
                raise ValueError("title must be a string or null")
            duplicate = db.scalar(
                select(Entry.id).where(
                    Entry.deleted_at.is_(None),
                    Entry.raw_content == raw_content,
                    Entry.title == title,
                )
            )
            if duplicate:
                skipped += 1
                continue
            payload = EntryCreate(
                title=title,
                raw_content=raw_content,
                content_format=str(record.get("content_format") or "markdown"),
                content_type=str(record.get("content_type") or "note"),
                source_uri=(
                    record.get("source_uri") if isinstance(record.get("source_uri"), str) else None
                ),
                event_time_start=record.get("event_time_start"),
                event_time_end=record.get("event_time_end"),
                is_pinned=bool(record.get("is_pinned", False)),
                is_favorite=bool(record.get("is_favorite", False)),
                importance=int(record.get("importance", 0)),
            )
            entry = create_entry(db, payload)
            created_ids.append(str(entry.id))
        except (ValueError, TypeError, SQLAlchemyError) as exc:
            db.rollback()
            if len(errors) < MAX_IMPORT_ERRORS:
                errors.append({"index": index, "error": str(exc)[:200]})
    return ImportResult(
        created_count=len(created_ids),
        skipped_count=skipped,
        entry_ids=created_ids,
        errors=errors,
    )
