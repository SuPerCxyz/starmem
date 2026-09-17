"""Generic external snapshot ingestion without implementing a concrete connector."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.external import ExternalSourceAdapter
from app.models import ContentUnit, ExternalItem, IngestionJob, Source


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def upsert_external_snapshot(
    db: Session, source: Source, normalized: dict[str, Any]
) -> tuple[ExternalItem, bool]:
    """Store one external snapshot and its ContentUnit; never creates an Entry."""
    external_id = str(normalized["external_id"])
    raw_content = str(normalized.get("raw_content") or "")
    content_hash = _content_hash(raw_content)
    item = db.scalar(
        select(ExternalItem).where(
            ExternalItem.source_id == source.id,
            ExternalItem.external_id == external_id,
        )
    )
    now = datetime.now(UTC)
    if item and item.content_hash == content_hash:
        item.last_synced_at = now
        return item, False
    if not item:
        item = ExternalItem(
            source_id=source.id,
            external_id=external_id,
            item_type=str(normalized.get("item_type") or "document"),
        )
        db.add(item)
        db.flush()
    item.external_parent_id = normalized.get("external_parent_id")
    item.item_type = str(normalized.get("item_type") or item.item_type)
    item.title = normalized.get("title")
    item.raw_content = raw_content
    item.external_created_at = normalized.get("external_created_at")
    item.external_updated_at = normalized.get("external_updated_at")
    item.content_hash = content_hash
    item.metadata_json = normalized.get("metadata_json") or {}
    item.last_synced_at = now
    unit = db.scalar(select(ContentUnit).where(ContentUnit.external_item_id == item.id))
    if not unit:
        unit = ContentUnit(
            owner_type="external_item",
            owner_id=item.id,
            source_id=source.id,
            external_item_id=item.id,
            unit_type=item.item_type,
            sequence=0,
            content=raw_content,
            event_time=normalized.get("external_updated_at")
            or normalized.get("external_created_at"),
            metadata_json=item.metadata_json,
        )
        db.add(unit)
    else:
        unit.content = raw_content
        unit.unit_type = item.item_type
        unit.event_time = normalized.get("external_updated_at") or normalized.get(
            "external_created_at"
        )
        unit.metadata_json = item.metadata_json
    return item, True


def sync_external_source(
    db: Session, source: Source, adapter: ExternalSourceAdapter, cursor: str | None = None
) -> int:
    count = 0
    for external_id in adapter.discover(cursor):
        raw_item = adapter.fetch_item(external_id)
        normalized = adapter.normalize(raw_item)
        upsert_external_snapshot(db, source, normalized)
        count += 1
    sync_cursor = adapter.get_cursor()
    job = db.scalar(
        select(IngestionJob).where(
            IngestionJob.source_id == source.id,
            IngestionJob.job_type == "sync",
            IngestionJob.sync_cursor == sync_cursor,
        )
    )
    if not job:
        job = IngestionJob(
            source_id=source.id,
            job_type="sync",
            sync_cursor=sync_cursor,
        )
        db.add(job)
    job.status = "done"
    job.finished_at = datetime.now(UTC)
    job.attempt += 1
    db.commit()
    return count
