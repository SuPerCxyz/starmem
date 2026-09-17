"""Local safety scan persistence for Raw Entries."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Entry, EntrySafetyScan
from app.secret_scanner import scan_secrets

SCANNER_VERSION = "local-v1"


def scan_entry(db: Session, entry: Entry) -> EntrySafetyScan:
    content_hash = hashlib.sha256(entry.raw_content.encode("utf-8")).hexdigest()
    findings = scan_secrets(entry.raw_content)
    scan = db.scalar(select(EntrySafetyScan).where(EntrySafetyScan.entry_id == entry.id))
    if not scan:
        scan = EntrySafetyScan(entry_id=entry.id, content_hash=content_hash)
        db.add(scan)
    scan.detected = bool(findings)
    scan.findings_json = findings
    scan.content_hash = content_hash
    scan.scanner_version = SCANNER_VERSION
    scan.scanned_at = datetime.now(UTC)
    db.flush()
    return scan


def get_entry_scan(db: Session, entry_id) -> EntrySafetyScan | None:
    return db.scalar(select(EntrySafetyScan).where(EntrySafetyScan.entry_id == entry_id))
