from __future__ import annotations

import io
import json
import zipfile
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.config import get_settings
from app.db import SessionLocal
from app.main import app
from app.models import Attachment, Entry, Source
from app.storage import remove_attachment, write_attachment


def _login(client: TestClient) -> dict[str, str]:
    settings = get_settings()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
    )
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def test_native_export_formats_attachment_archive_and_import_dedup(monkeypatch):
    monkeypatch.setattr("app.services.entries._enqueue", lambda entry_id: None)
    marker = f"portability-{uuid4()}"
    imported_marker = f"imported-{uuid4()}"
    entry_id: UUID | None = None
    imported_id: UUID | None = None
    storage_key: str | None = None
    try:
        with SessionLocal() as db:
            source = db.scalar(select(Source).where(Source.is_native.is_(True)))
            assert source
            entry = Entry(
                source_id=source.id,
                title=f"Portable {marker}",
                raw_content=f"# {marker}\nportable content",
                content_type="note",
                source_uri="https://example.com/portable",
            )
            db.add(entry)
            db.flush()
            entry_id = entry.id
            storage_key, digest = write_attachment(b"portable attachment", "../portable.txt")
            db.add(
                Attachment(
                    entry_id=entry.id,
                    storage_key=storage_key,
                    original_filename="portable.txt",
                    media_type="text/plain",
                    size_bytes=19,
                    content_hash=digest,
                    processing_status="processed",
                )
            )
            db.commit()

        with TestClient(app) as client:
            headers = _login(client)
            exported_json = client.get("/api/v1/export", params={"format": "json"})
            assert exported_json.status_code == 200, exported_json.text
            payload = exported_json.json()
            record = next(item for item in payload["entries"] if item["id"] == str(entry_id))
            assert record["raw_content"] == f"# {marker}\nportable content"
            assert record["source_uri"] == "https://example.com/portable"
            assert "chat_api_key" not in exported_json.text.lower()

            exported_jsonl = client.get("/api/v1/export", params={"format": "jsonl"})
            assert exported_jsonl.status_code == 200
            assert any(
                json.loads(line)["id"] == str(entry_id)
                for line in exported_jsonl.text.splitlines()
                if line.strip()
            )

            exported_markdown = client.get("/api/v1/export", params={"format": "markdown"})
            assert exported_markdown.status_code == 200
            assert marker in exported_markdown.text
            assert f"starmem-entry-id: {entry_id}" in exported_markdown.text

            exported_zip = client.get("/api/v1/export", params={"format": "zip"})
            assert exported_zip.status_code == 200
            with zipfile.ZipFile(io.BytesIO(exported_zip.content)) as archive:
                names = archive.namelist()
                assert "starmem-export.json" in names
                attachment_name = next(
                    name for name in names if name.startswith(f"attachments/{entry_id}/")
                )
                assert archive.read(attachment_name) == b"portable attachment"

            import_payload = {
                "format": "starmem.native.v1",
                "entries": [
                    {
                        "title": f"Imported {imported_marker}",
                        "raw_content": imported_marker,
                        "content_type": "note",
                    }
                ],
            }
            imported = client.post(
                "/api/v1/import",
                headers=headers,
                files={
                    "file": (
                        "native.json",
                        json.dumps(import_payload).encode(),
                        "application/json",
                    )
                },
            )
            assert imported.status_code == 201, imported.text
            assert imported.json()["created_count"] == 1
            assert imported.json()["skipped_count"] == 0
            imported_id = UUID(imported.json()["entry_ids"][0])

            repeated = client.post(
                "/api/v1/import",
                headers=headers,
                files={
                    "file": (
                        "native.json",
                        json.dumps(import_payload).encode(),
                        "application/json",
                    )
                },
            )
            assert repeated.status_code == 201, repeated.text
            assert repeated.json()["created_count"] == 0
            assert repeated.json()["skipped_count"] == 1

            bad_extension = client.post(
                "/api/v1/import",
                headers=headers,
                files={"file": ("native.txt", b"{}", "text/plain")},
            )
            assert bad_extension.status_code == 422
            bad_format = client.post(
                "/api/v1/import",
                headers=headers,
                files={
                    "file": (
                        "foreign.json",
                        b'{"format":"foreign.v1","entries":[]}',
                        "application/json",
                    )
                },
            )
            assert bad_format.status_code == 422
    finally:
        if storage_key:
            remove_attachment(storage_key)
        with SessionLocal() as db:
            ids = [item for item in (entry_id, imported_id) if item]
            if ids:
                db.execute(delete(Entry).where(Entry.id.in_(ids)))
            db.commit()
