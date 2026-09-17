from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.config import get_settings
from app.db import SessionLocal
from app.main import app
from app.models import Attachment, ContentUnit, Entry, IngestionJob
from app.providers import TesseractOCRProvider
from app.services import ingestion
from app.services.import_parsers import (
    FetchedPage,
    ImportParseError,
    extract_html,
    fetch_url,
    parse_file,
    validate_url_target,
)
from app.storage import remove_attachment


def _login(client: TestClient) -> dict[str, str]:
    settings = get_settings()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
    )
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def test_text_pdf_html_and_local_ocr_parsers(monkeypatch):
    formats = (
        ("notes.md", "text/markdown", "# 标题\n原始内容"),
        ("settings.json", "application/json", '{"enabled": true}'),
        ("config.yaml", "text/yaml", "service: starmem\n"),
        ("debug.log", "text/x-log", "ERROR multipath path missing\n"),
    )
    for filename, media_type, expected in formats:
        content_format, content_type, units, _ = parse_file(
            expected.encode(), filename=filename, media_type=media_type
        )
        assert units[0].content == expected
        assert units[0].unit_type == "file_text"
        assert content_format != ""
        assert content_type == "document"

    import fitz

    document = fitz.open()
    first = document.new_page()
    first.insert_text((72, 72), "page one evidence")
    second = document.new_page()
    second.insert_text((72, 72), "page two evidence")
    pdf_data = document.tobytes()
    document.close()
    _, _, pdf_units, metadata = parse_file(
        pdf_data, filename="evidence.pdf", media_type="application/pdf"
    )
    assert metadata["page_count"] == 2
    assert [unit.metadata["page_number"] for unit in pdf_units] == [1, 2]
    assert pdf_units[1].content == "page two evidence"

    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (900, 180), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
    draw.text((24, 48), "StarMem 123", fill="black", font=font)
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    ocr_text = TesseractOCRProvider().extract(
        image_bytes.getvalue(), language="eng", timeout_seconds=15
    )
    assert "StarMem" in ocr_text

    title, body = extract_html(
        b"<html><head><title>Imported page</title><script>secret()</script></head>"
        b"<body><h1>Evidence</h1><p>Visible text</p></body></html>",
        "https://example.com/item",
    )
    assert title == "Imported page"
    assert "Visible text" in body
    assert "secret" not in body

    with pytest.raises(ImportParseError, match="publicly routable"):
        validate_url_target("http://127.0.0.1:8080/private")

    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"<title>Mock</title><p>mock page</p>",
        )
    )
    monkeypatch.setattr("app.services.import_parsers.validate_url_target", lambda url: None)
    fetched = fetch_url(
        "https://example.com/item",
        client_factory=lambda **kwargs: httpx.Client(transport=transport, **kwargs),
    )
    assert isinstance(fetched, FetchedPage)
    assert fetched.title == "Mock"
    assert "mock page" in fetched.text

    redirect_transport = httpx.MockTransport(
        lambda request: httpx.Response(302, headers={"location": "/next"})
    )
    monkeypatch.setattr(
        "app.services.import_parsers.get_settings",
        lambda: SimpleNamespace(url_max_redirects=1, url_timeout_seconds=5, max_url_bytes=1024),
    )
    with pytest.raises(ImportParseError, match="redirect limit"):
        fetch_url(
            "https://example.com/start",
            client_factory=lambda **kwargs: httpx.Client(transport=redirect_transport, **kwargs),
        )


def test_file_import_is_idempotent_and_reaches_search_and_download(monkeypatch):
    monkeypatch.setattr(ingestion, "_enqueue", lambda job: None)
    entry_id: UUID | None = None
    storage_key: str | None = None
    key = f"p1-file-{uuid4()}"
    try:
        with TestClient(app) as client:
            headers = _login(client)
            response = client.post(
                "/api/v1/ingest/file",
                headers={**headers, "Idempotency-Key": key},
                files={"file": ("p1-notes.md", b"# Imported\nimportant marker", "text/markdown")},
            )
            assert response.status_code == 202, response.text
            first = response.json()
            entry_id = UUID(first["entry_id"])
            assert first["status"] == "new"
            assert len(first["attachments"]) == 1

            repeated = client.post(
                "/api/v1/ingest/file",
                headers={**headers, "Idempotency-Key": key},
                files={"file": ("different.md", b"different", "text/markdown")},
            )
            assert repeated.status_code == 202, repeated.text
            assert repeated.json()["job_id"] == first["job_id"]
            assert repeated.json()["entry_id"] == first["entry_id"]

            with SessionLocal() as db:
                assert ingestion.process_job(db, UUID(first["job_id"])) == entry_id
                unit = db.scalar(
                    select(ContentUnit).where(
                        ContentUnit.entry_id == entry_id,
                        ContentUnit.unit_type == "file_text",
                    )
                )
                assert unit and unit.content == "# Imported\nimportant marker"
                attachment = db.scalar(select(Attachment).where(Attachment.entry_id == entry_id))
                assert attachment
                storage_key = attachment.storage_key

            inbox = client.get("/api/v1/inbox")
            assert inbox.status_code == 200
            assert inbox.json()[0]["status"] == "processed"
            download = client.get(f"/api/v1/attachments/{attachment.id}")
            assert download.status_code == 200
            assert download.content == b"# Imported\nimportant marker"
            search = client.get(
                "/api/v1/search", params={"q": "important marker", "mode": "fulltext"}
            )
            assert search.status_code == 200
            assert any(item["entry_id"] == str(entry_id) for item in search.json()["items"])
            matching = next(
                item for item in search.json()["items"] if item["entry_id"] == str(entry_id)
            )
            assert matching["attachment_id"] == str(attachment.id)
            assert matching["provenance_type"] == "file_text"
    finally:
        if storage_key:
            remove_attachment(storage_key)
        if entry_id:
            with SessionLocal() as db:
                db.execute(delete(Entry).where(Entry.id == entry_id))
                db.commit()


def test_url_snapshot_creates_native_entry_and_provenance(monkeypatch):
    monkeypatch.setattr(ingestion, "_enqueue", lambda job: None)
    monkeypatch.setattr(
        ingestion,
        "fetch_url",
        lambda url: FetchedPage(
            original_url=url,
            final_url="https://example.com/final",
            title="Imported article",
            text="url evidence marker",
            snapshot=b"<title>Imported article</title><p>url evidence marker</p>",
            media_type="text/html",
        ),
    )
    entry_id: UUID | None = None
    storage_key: str | None = None
    try:
        with SessionLocal() as db:
            result = ingestion.submit_url(
                db,
                url="https://example.com/article",
                title=None,
                idempotency_key=f"p1-url-{uuid4()}",
            )
            entry_id = result.job.entry_id
            assert ingestion.process_job(db, result.job.id) == entry_id
            job = db.get(IngestionJob, result.job.id)
            attachment = db.scalar(select(Attachment).where(Attachment.entry_id == entry_id))
            entry = db.get(Entry, entry_id)
            unit = db.scalar(
                select(ContentUnit).where(
                    ContentUnit.entry_id == entry_id, ContentUnit.unit_type == "web_page"
                )
            )
            assert job and job.status == "processed"
            assert (
                attachment and attachment.metadata_json["final_url"] == "https://example.com/final"
            )
            assert entry and entry.source_uri == "https://example.com/article"
            assert unit and unit.metadata_json["original_url"] == "https://example.com/article"
            storage_key = attachment.storage_key
    finally:
        if storage_key:
            remove_attachment(storage_key)
        if entry_id:
            with SessionLocal() as db:
                db.execute(delete(Entry).where(Entry.id == entry_id))
                db.commit()


def test_failed_ocr_retains_attachment_and_retry_reuses_entry(monkeypatch):
    monkeypatch.setattr(ingestion, "_enqueue", lambda job: None)
    monkeypatch.setattr(ingestion, "get_ocr_provider", lambda: None)
    entry_id: UUID | None = None
    job_id: UUID | None = None
    storage_key: str | None = None
    try:
        with SessionLocal() as db:
            result = ingestion.submit_file(
                db,
                data=b"not-an-image",
                filename="broken.png",
                media_type="image/png",
                title="Broken image",
                idempotency_key=f"p1-ocr-{uuid4()}",
            )
            entry_id = result.job.entry_id
            job_id = result.job.id
            storage_key = result.attachments[0].storage_key
            assert ingestion.process_job(db, job_id) is None
            failed = db.get(IngestionJob, job_id)
            assert failed and failed.status == "failed" and failed.error_code == "ocr_unavailable"
            retried = ingestion.retry_job(db, job_id)
            assert retried and retried.job.id == job_id
            assert retried.job.entry_id == entry_id
            assert retried.attachments[0].id == result.attachments[0].id
            assert retried.job.status == "new"
    finally:
        if storage_key:
            remove_attachment(storage_key)
        if entry_id:
            with SessionLocal() as db:
                db.execute(delete(Entry).where(Entry.id == entry_id))
                db.commit()


def test_retry_claim_allows_only_one_processing_attempt(monkeypatch):
    monkeypatch.setattr(ingestion, "_enqueue", lambda job: None)
    monkeypatch.setattr(ingestion, "get_ocr_provider", lambda: None)
    entry_id: UUID | None = None
    job_id: UUID | None = None
    storage_key: str | None = None
    try:
        with SessionLocal() as db:
            result = ingestion.submit_file(
                db,
                data=b"not-an-image",
                filename="concurrent.png",
                media_type="image/png",
                title="Concurrent image",
                idempotency_key=f"p1-concurrent-{uuid4()}",
            )
            entry_id = result.job.entry_id
            job_id = result.job.id
            storage_key = result.attachments[0].storage_key
            assert ingestion.process_job(db, job_id) is None
            first = ingestion.retry_job(db, job_id)
            second = ingestion.retry_job(db, job_id)
            assert first and second and first.job.id == second.job.id == job_id
            assert ingestion.process_job(db, job_id) is None
            final = db.get(IngestionJob, job_id)
            assert final and final.attempt == 2 and final.status == "failed"
    finally:
        if storage_key:
            remove_attachment(storage_key)
        if entry_id:
            with SessionLocal() as db:
                db.execute(delete(Entry).where(Entry.id == entry_id))
                db.commit()


def test_import_api_rejects_unsupported_types_and_unsafe_urls():
    with TestClient(app) as client:
        headers = _login(client)
        unsupported = client.post(
            "/api/v1/ingest/file",
            headers=headers,
            files={"file": ("payload.exe", b"binary", "application/octet-stream")},
        )
        assert unsupported.status_code == 422
        unsafe = client.post(
            "/api/v1/ingest/url",
            headers=headers,
            json={"url": "ftp://example.com/file"},
        )
        assert unsafe.status_code == 422
