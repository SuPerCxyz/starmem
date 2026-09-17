"""Native URL/file ingestion and Inbox lifecycle services."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Attachment, ContentUnit, Entry, EntryVersion, IngestionJob
from app.providers import get_ocr_provider
from app.services.entries import _create_jobs, _next_version_number, get_native_source
from app.services.import_parsers import (
    ImportParseError,
    ParsedUnit,
    fetch_url,
    parse_file,
    validate_url_syntax,
)
from app.services.safety import scan_entry
from app.storage import StorageError, read_attachment, remove_attachment, write_attachment

IMPORT_KINDS = {"url", "file"}
IMPORT_STATUSES = {"new", "processing", "processed", "failed"}


@dataclass(frozen=True)
class ImportResult:
    job: IngestionJob
    attachments: list[Attachment]


def _clean_idempotency_key(value: str | None) -> str | None:
    if value is None:
        return None
    value = " ".join(value.strip().split())
    if not value:
        return None
    if len(value) > 255:
        raise ImportParseError("idempotency_key_too_long", "Idempotency key is too long")
    return value


def _existing_job(db: Session, key: str | None) -> IngestionJob | None:
    if not key:
        return None
    return db.scalar(select(IngestionJob).where(IngestionJob.idempotency_key == key))


def _new_entry(
    db: Session,
    *,
    title: str | None,
    content_format: str,
    content_type: str,
    source_uri: str | None,
    source_id: UUID,
) -> Entry:
    entry = Entry(
        source_id=source_id,
        title=title,
        raw_content="",
        content_format=content_format,
        content_type=content_type,
        source_uri=source_uri,
        ai_status="pending",
    )
    db.add(entry)
    db.flush()
    db.add(
        EntryVersion(
            entry_id=entry.id,
            version_number=1,
            raw_content="",
            title=title,
            change_source="ingestion",
        )
    )
    _create_jobs(db, entry)
    return entry


def _add_pending_unit(db: Session, entry: Entry, source_id: UUID, job_id: UUID) -> None:
    db.add(
        ContentUnit(
            owner_type="entry",
            owner_id=entry.id,
            source_id=source_id,
            entry_id=entry.id,
            unit_type="import_pending",
            sequence=0,
            content="",
            metadata_json={"ingestion_job_id": str(job_id), "pending": True},
        )
    )


def _enqueue(job: IngestionJob) -> None:
    try:
        from app.worker import process_ingestion

        process_ingestion.send(str(job.id))
    except Exception as exc:
        job.status = "failed"
        job.phase = "queue"
        job.error_code = "queue_unavailable"
        job.error = "Import queue is unavailable; retry later."
        job.finished_at = datetime.now(UTC)
        job.metadata_json = {**(job.metadata_json or {}), "queue_error": type(exc).__name__}
        return


def _commit_and_enqueue(db: Session, job: IngestionJob) -> None:
    db.commit()
    db.refresh(job)
    _enqueue(job)
    db.commit()


def submit_file(
    db: Session,
    *,
    data: bytes,
    filename: str,
    media_type: str | None,
    title: str | None,
    idempotency_key: str | None,
) -> ImportResult:
    key = _clean_idempotency_key(idempotency_key)
    if existing := _existing_job(db, key):
        return _result(db, existing)
    source = get_native_source(db)
    from app.services.import_parsers import detect_file_format

    content_format, kind = detect_file_format(filename, media_type)
    content_type = {"pdf": "pdf", "image": "image"}.get(kind, "document")
    storage_key, digest = write_attachment(data, filename)
    attachment: Attachment | None = None
    try:
        entry = _new_entry(
            db,
            title=title or Path(filename).name,
            content_format=content_format,
            content_type=content_type,
            source_uri=None,
            source_id=source.id,
        )
        attachment = Attachment(
            entry_id=entry.id,
            storage_key=storage_key,
            original_filename=Path(filename).name[:255] or "attachment",
            media_type=(media_type or "application/octet-stream").split(";", 1)[0].strip(),
            size_bytes=len(data),
            content_hash=digest,
            metadata_json={"input_kind": "file", "format": content_format},
        )
        db.add(attachment)
        db.flush()
        job = IngestionJob(
            source_id=source.id,
            entry_id=entry.id,
            attachment_id=attachment.id,
            job_type="import",
            input_kind="file",
            status="new",
            phase="queued",
            idempotency_key=key,
            original_name=attachment.original_filename,
            media_type=attachment.media_type,
            metadata_json={"format": content_format},
        )
        db.add(job)
        db.flush()
        _add_pending_unit(db, entry, source.id, job.id)
        _commit_and_enqueue(db, job)
        return _result(db, job)
    except IntegrityError:
        db.rollback()
        remove_attachment(storage_key)
        if key and (existing := _existing_job(db, key)):
            return _result(db, existing)
        raise
    except Exception:
        db.rollback()
        remove_attachment(storage_key)
        raise


def submit_url(
    db: Session,
    *,
    url: str,
    title: str | None,
    idempotency_key: str | None,
) -> ImportResult:
    key = _clean_idempotency_key(idempotency_key)
    if existing := _existing_job(db, key):
        return _result(db, existing)
    validate_url_syntax(url)
    source = get_native_source(db)
    entry = _new_entry(
        db,
        title=title,
        content_format="html",
        content_type="web_page",
        source_uri=url.strip(),
        source_id=source.id,
    )
    job = IngestionJob(
        source_id=source.id,
        entry_id=entry.id,
        job_type="import",
        input_kind="url",
        status="new",
        phase="queued",
        idempotency_key=key,
        original_name=url.strip()[:2_000],
        media_type="text/html",
        source_uri=url.strip(),
        metadata_json={"original_url": url.strip()},
    )
    db.add(job)
    db.flush()
    _add_pending_unit(db, entry, source.id, job.id)
    _commit_and_enqueue(db, job)
    return _result(db, job)


def _result(db: Session, job: IngestionJob) -> ImportResult:
    attachments = db.scalars(
        select(Attachment)
        .where(Attachment.entry_id == job.entry_id)
        .order_by(Attachment.created_at)
    ).all()
    return ImportResult(job=job, attachments=attachments)


def list_jobs(db: Session, *, status: str | None = None, limit: int = 100) -> list[ImportResult]:
    statement = (
        select(IngestionJob)
        .where(IngestionJob.input_kind.in_(IMPORT_KINDS))
        .order_by(IngestionJob.created_at.desc())
        .limit(limit)
    )
    if status:
        statement = statement.where(IngestionJob.status == status)
    jobs = db.scalars(statement).all()
    return [_result(db, job) for job in jobs]


def get_job(db: Session, job_id: UUID) -> ImportResult | None:
    job = db.scalar(
        select(IngestionJob).where(
            IngestionJob.id == job_id, IngestionJob.input_kind.in_(IMPORT_KINDS)
        )
    )
    return _result(db, job) if job else None


def retry_job(db: Session, job_id: UUID) -> ImportResult | None:
    job = db.scalar(
        select(IngestionJob)
        .where(IngestionJob.id == job_id, IngestionJob.input_kind.in_(IMPORT_KINDS))
        .with_for_update()
    )
    if not job:
        return None
    if job.status == "processing":
        raise ValueError("Import is already processing")
    if job.status == "processed":
        return _result(db, job)
    job.status = "new"
    job.phase = "queued"
    job.error_code = None
    job.error = None
    job.finished_at = None
    db.commit()
    _enqueue(job)
    db.commit()
    return _result(db, job)


def correct_job(
    db: Session,
    *,
    job_id: UUID,
    title: str | None,
    content_type: str | None,
) -> ImportResult | None:
    """Apply a user correction to the imported Entry without touching attachments."""
    job = db.scalar(
        select(IngestionJob)
        .where(IngestionJob.id == job_id, IngestionJob.input_kind.in_(IMPORT_KINDS))
        .with_for_update()
    )
    if not job:
        return None
    if job.status == "processing":
        raise ValueError("Import is still processing")
    entry = db.get(Entry, job.entry_id)
    if not entry or entry.deleted_at is not None:
        raise ValueError("Imported Entry is not available")
    changed = False
    if title is not None:
        normalized = " ".join(title.strip().split())
        if normalized != (entry.title or ""):
            entry.title = normalized or None
            changed = True
    if content_type is not None:
        normalized_type = " ".join(content_type.strip().split())
        if not normalized_type:
            raise ValueError("Content type cannot be blank")
        if normalized_type != entry.content_type:
            entry.content_type = normalized_type
            changed = True
    if changed:
        db.add(
            EntryVersion(
                entry_id=entry.id,
                version_number=_next_version_number(db, entry.id),
                raw_content=entry.raw_content,
                title=entry.title,
                change_source="user",
            )
        )
        job.metadata_json = {
            **(job.metadata_json or {}),
            "user_corrected": True,
        }
        db.commit()
    return _result(db, job)


def _claim_job(db: Session, job_id: UUID) -> IngestionJob | None:
    job = db.scalar(
        select(IngestionJob)
        .where(IngestionJob.id == job_id, IngestionJob.input_kind.in_(IMPORT_KINDS))
        .with_for_update()
    )
    if not job or job.status in {"processing", "processed"}:
        return None
    if job.status not in {"new", "failed"}:
        return None
    job.status = "processing"
    job.phase = "fetching" if job.input_kind == "url" else "parsing"
    job.attempt += 1
    job.started_at = datetime.now(UTC)
    job.finished_at = None
    job.error_code = None
    job.error = None
    db.commit()
    return job


def _remove_job_units(db: Session, entry_id: UUID, job_id: UUID) -> None:
    units = db.scalars(select(ContentUnit).where(ContentUnit.entry_id == entry_id)).all()
    marker = str(job_id)
    for unit in units:
        metadata = unit.metadata_json or {}
        if unit.unit_type == "import_pending" or metadata.get("ingestion_job_id") == marker:
            db.delete(unit)


def _persist_result(
    db: Session,
    job: IngestionJob,
    *,
    units: list[ParsedUnit],
    content_format: str,
    content_type: str,
    title: str | None,
    attachment: Attachment | None,
    metadata: dict[str, object],
) -> None:
    entry = db.get(Entry, job.entry_id)
    if not entry:
        raise ImportParseError("entry_missing", "Imported Entry no longer exists")
    source_id = job.source_id
    _remove_job_units(db, entry.id, job.id)
    for unit in units:
        db.add(
            ContentUnit(
                owner_type="entry",
                owner_id=entry.id,
                source_id=source_id,
                entry_id=entry.id,
                attachment_id=attachment.id if attachment else None,
                unit_type=unit.unit_type,
                sequence=unit.sequence,
                content=unit.content,
                event_time=entry.event_time_start,
                metadata_json={
                    **unit.metadata,
                    "ingestion_job_id": str(job.id),
                    "input_kind": job.input_kind,
                    "attachment_id": str(attachment.id) if attachment else None,
                },
            )
        )
    raw_content = (
        units[0].content if len(units) == 1 else "\n\n".join(unit.content for unit in units)
    )
    entry.raw_content = raw_content
    entry.content_format = content_format
    entry.content_type = content_type
    if title and not entry.title:
        entry.title = title
    db.add(
        EntryVersion(
            entry_id=entry.id,
            version_number=_next_version_number(db, entry.id),
            raw_content=raw_content,
            title=entry.title,
            change_source="ingestion",
        )
    )
    entry.ai_generation += 1
    entry.ai_status = "pending"
    _create_jobs(db, entry)
    scan_entry(db, entry)
    if attachment:
        attachment.processing_status = "processed"
        attachment.metadata_json = {**(attachment.metadata_json or {}), **metadata}
    job.metadata_json = {**(job.metadata_json or {}), **metadata}
    job.phase = "complete"
    job.status = "processed"
    job.error_code = None
    job.error = None
    job.finished_at = datetime.now(UTC)


def process_job(db: Session, job_id: UUID) -> UUID | None:
    job = _claim_job(db, job_id)
    if not job:
        return None
    created_storage_key: str | None = None
    attachment: Attachment | None = None
    try:
        if job.input_kind == "url":
            fetched = fetch_url(job.source_uri or "")
            job.phase = "parsing"
            digest = hashlib.sha256(fetched.snapshot).hexdigest()
            attachment = db.scalar(
                select(Attachment).where(
                    Attachment.entry_id == job.entry_id,
                    Attachment.content_hash == digest,
                )
            )
            if not attachment:
                attachment_result = write_attachment(fetched.snapshot, "web-page.html")
                created_storage_key = attachment_result[0]
                attachment = Attachment(
                    entry_id=job.entry_id,
                    storage_key=attachment_result[0],
                    original_filename="web-page.html",
                    media_type=fetched.media_type or "text/html",
                    size_bytes=len(fetched.snapshot),
                    content_hash=attachment_result[1],
                    processing_status="processing",
                    metadata_json={
                        "original_url": fetched.original_url,
                        "final_url": fetched.final_url,
                        "title": fetched.title,
                    },
                )
                db.add(attachment)
                db.flush()
            else:
                attachment.processing_status = "processing"
            units = [
                ParsedUnit(
                    content=fetched.text,
                    unit_type="web_page",
                    sequence=0,
                    metadata={
                        "original_url": fetched.original_url,
                        "final_url": fetched.final_url,
                        "title": fetched.title,
                    },
                )
            ]
            _persist_result(
                db,
                job,
                units=units,
                content_format="html",
                content_type="web_page",
                title=fetched.title,
                attachment=attachment,
                metadata={"final_url": fetched.final_url, "title": fetched.title},
            )
            job.attachment_id = attachment.id
            job.media_type = fetched.media_type
        else:
            attachment = db.get(Attachment, job.attachment_id)
            if not attachment:
                raise ImportParseError("attachment_missing", "Original attachment is unavailable")
            job.phase = "parsing"
            path = read_attachment(attachment.storage_key)
            data = path.read_bytes()
            if (
                len(data) != attachment.size_bytes
                or hashlib.sha256(data).hexdigest() != attachment.content_hash
            ):
                raise ImportParseError(
                    "attachment_changed", "Original attachment integrity check failed"
                )
            parsed_format, parsed_type, units, metadata = parse_file(
                data,
                filename=attachment.original_filename,
                media_type=attachment.media_type,
                ocr_provider=get_ocr_provider(),
            )
            _persist_result(
                db,
                job,
                units=units,
                content_format=parsed_format,
                content_type=parsed_type,
                title=None,
                attachment=attachment,
                metadata=metadata,
            )
        db.commit()
        return job.entry_id
    except ImportParseError as exc:
        db.rollback()
        if created_storage_key:
            remove_attachment(created_storage_key)
        _mark_failed(
            db,
            job_id,
            code=exc.code,
            message=str(exc),
            attachment_id=attachment.id if attachment else None,
        )
    except (OSError, StorageError) as exc:
        db.rollback()
        if created_storage_key:
            remove_attachment(created_storage_key)
        _mark_failed(
            db,
            job_id,
            code="storage_failed",
            message=str(exc),
            attachment_id=attachment.id if attachment else None,
        )
    except Exception as exc:
        db.rollback()
        if created_storage_key:
            remove_attachment(created_storage_key)
        _mark_failed(
            db,
            job_id,
            code="processing_failed",
            message=type(exc).__name__,
            attachment_id=attachment.id if attachment else None,
        )
    return None


def _mark_failed(
    db: Session,
    job_id: UUID,
    *,
    code: str,
    message: str,
    attachment_id: UUID | None,
) -> None:
    job = db.get(IngestionJob, job_id)
    if not job:
        return
    job.status = "failed"
    job.phase = job.phase or "processing"
    job.error_code = code
    job.error = message[:500]
    job.finished_at = datetime.now(UTC)
    if attachment_id:
        attachment = db.get(Attachment, attachment_id)
        if attachment:
            attachment.processing_status = "failed"
            attachment.metadata_json = {
                **(attachment.metadata_json or {}),
                "last_error_code": code,
            }
    db.commit()
