from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.config import get_settings
from app.db import SessionLocal
from app.main import app
from app.models import Entry
from app.services import entries as entry_service


def test_raw_capture_versions_search_and_soft_delete(monkeypatch):
    created_id: UUID | None = None
    marker = f"phase1-{uuid4()}"
    raw = (
        f"# {marker}\n\n"
        "```bash\niscsiadm -m node \\\n-T iqn.example \\\n-o delete\n```\n\n"
        + ("2026-09-15T10:00:00 INFO multipath path retained\n" * 600)
        + "WWN=naa.6001405abcdef1234567890abcdef12\n"
    )
    assert len(raw) > 20_000
    monkeypatch.setattr(entry_service, "_enqueue", lambda entry_id: None)
    settings = get_settings()
    with TestClient(app) as client:
        login = client.post(
            "/api/v1/auth/login",
            json={"email": settings.admin_email, "password": settings.admin_password},
        )
        assert login.status_code == 200, login.text
        csrf = login.json()["csrf_token"]
        write_headers = {"X-CSRF-Token": csrf}

        created = client.post(
            "/api/v1/entries",
            headers=write_headers,
            json={"raw_content": raw, "content_format": "markdown"},
        )
        assert created.status_code == 201, created.text
        created_id = UUID(created.json()["id"])
        assert created.json()["raw_content"] == raw

        timeline = client.get("/api/v1/entries", params={"limit": 100})
        assert timeline.status_code == 200
        assert any(item["id"] == str(created_id) for item in timeline.json()["items"])

        search = client.get(
            "/api/v1/search",
            params={"q": "naa.6001405abcdef1234567890abcdef12", "mode": "fulltext"},
        )
        assert search.status_code == 200, search.text
        assert search.json()["items"][0]["entry_id"] == str(created_id)
        assert search.json()["items"][0]["exact_match"] is True

        current = raw
        for index in range(1, 4):
            current = f"{current}\nedit-{index}"
            updated = client.patch(
                f"/api/v1/entries/{created_id}",
                headers=write_headers,
                json={"raw_content": current},
            )
            assert updated.status_code == 200, updated.text
        versions = client.get(f"/api/v1/entries/{created_id}/versions")
        assert versions.status_code == 200
        assert [item["version_number"] for item in versions.json()] == [4, 3, 2, 1]
        diff = client.get(f"/api/v1/entries/{created_id}/versions/3/diff")
        assert diff.status_code == 200
        assert "edit-2" in diff.json()["diff"]
        restored = client.post(f"/api/v1/entries/{created_id}/restore/2", headers=write_headers)
        assert restored.status_code == 200
        assert restored.json()["raw_content"] == raw + "\nedit-1"

        deleted = client.delete(f"/api/v1/entries/{created_id}", headers=write_headers)
        assert deleted.status_code == 204
        assert client.get(f"/api/v1/entries/{created_id}").status_code == 404
        assert not any(
            item["id"] == str(created_id)
            for item in client.get("/api/v1/entries", params={"limit": 100}).json()["items"]
        )
        assert not client.get("/api/v1/search", params={"q": marker, "mode": "fulltext"}).json()[
            "items"
        ]

    if created_id:
        with SessionLocal() as db:
            db.execute(delete(Entry).where(Entry.id == created_id))
            db.commit()
