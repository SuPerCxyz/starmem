"""End-to-end smoke check for the local Compose stack."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from uuid import uuid4

import httpx
from sqlalchemy import delete

from app.config import get_settings
from app.db import SessionLocal
from app.models import AskQuery, Entry, Memory


def main() -> int:
    settings = get_settings()
    marker = f"integration-smoke-{uuid4()}"
    smoke_started_at = datetime.now(UTC)
    entry_id: str | None = None
    with httpx.Client(base_url="http://api:8000", timeout=60) as client:
        login = client.post(
            "/api/v1/auth/login",
            json={"email": settings.admin_email, "password": settings.admin_password},
        )
        login.raise_for_status()
        csrf = login.json()["csrf_token"]
        write_headers = {"X-CSRF-Token": csrf}
        created = client.post(
            "/api/v1/entries",
            headers=write_headers,
            json={"raw_content": f"# {marker}\n\nV100 最终固定限制到 150W。"},
        )
        created.raise_for_status()
        entry_id = created.json()["id"]
        candidate = client.post(
            f"/api/v1/entries/{entry_id}/memory-candidates",
            headers=write_headers,
            json={
                "subject": "V100",
                "predicate": "power_limit",
                "value": "150W",
                "memory_text": "V100 当前长期功耗限制为 150W。",
                "confidence": 0.98,
            },
        )
        candidate.raise_for_status()
        jobs = client.get("/api/v1/ai-jobs", params={"entry_id": entry_id})
        jobs.raise_for_status()
        assert len(jobs.json()) >= 11
        timeline = client.get("/api/v1/entries")
        timeline.raise_for_status()
        assert any(item["id"] == entry_id for item in timeline.json()["items"])
        search = client.get("/api/v1/search", params={"q": marker, "mode": "fulltext"})
        search.raise_for_status()
        assert search.json()["items"][0]["entry_id"] == entry_id
        asked = client.post("/api/v1/ask", json={"query": "V100 最后设置多少瓦？"})
        asked.raise_for_status()
        answer = asked.json()
        assert answer["sources"] and any(
            source["entry_id"] == entry_id for source in answer["sources"]
        )
        deleted = client.delete(f"/api/v1/entries/{entry_id}", headers=write_headers)
        deleted.raise_for_status()
        assert client.get(f"/api/v1/entries/{entry_id}").status_code == 404
        restored = client.post(f"/api/v1/entries/{entry_id}/undelete", headers=write_headers)
        restored.raise_for_status()
        assert restored.json()["id"] == entry_id
    with SessionLocal() as db:
        db.execute(delete(Memory).where(Memory.source_entry_id == entry_id))
        db.execute(delete(Entry).where(Entry.id == entry_id))
        # The smoke Ask call is logged by design; remove only this run's fixture log.
        db.execute(
            delete(AskQuery).where(
                AskQuery.query_text == "V100 最后设置多少瓦？",
                AskQuery.created_at >= smoke_started_at,
            )
        )
        db.commit()
    print("integration-smoke: passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
