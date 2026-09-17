from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.ai_tasks import run_ai_job
from app.config import get_settings
from app.db import SessionLocal
from app.main import app
from app.models import (
    AIJob,
    ContentUnit,
    Entity,
    Entry,
    EntryEntity,
    Memory,
    MemoryCandidate,
    PromptTestCase,
    PromptVersion,
    Source,
)
from app.providers import ProviderNotConfigured


def _login(client: TestClient) -> dict[str, str]:
    settings = get_settings()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
    )
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def _native_source(db) -> Source:
    source = db.scalar(select(Source).where(Source.is_native.is_(True)))
    assert source
    return source


def _make_entry(db, marker: str, **kwargs) -> Entry:
    kwargs.setdefault("content_type", "note")
    entry = Entry(
        source_id=_native_source(db).id,
        title=f"Entry {marker}",
        raw_content=f"{marker}\nfixture content",
        **kwargs,
    )
    db.add(entry)
    db.flush()
    db.add(
        ContentUnit(
            owner_type="entry",
            owner_id=entry.id,
            source_id=entry.source_id,
            entry_id=entry.id,
            unit_type="entry",
            content=entry.raw_content,
        )
    )
    db.flush()
    return entry


class _NotConfiguredChatProvider:
    name = "openai-compatible"
    model = "unconfigured"

    def complete(self, *_args, **_kwargs):
        raise ProviderNotConfigured("Chat provider credentials are not configured")


def test_chat_jobs_are_skipped_not_failed_when_provider_unconfigured():
    marker = f"skipchat-{uuid4()}"
    entry_id: UUID | None = None
    try:
        with SessionLocal() as db:
            entry = _make_entry(db, marker)
            job = AIJob(entry_id=entry.id, job_type="summarize", generation=entry.ai_generation)
            db.add(job)
            db.commit()
            assert not run_ai_job(db, entry, job, chat_provider=_NotConfiguredChatProvider())
            db.refresh(job)
            assert job.status == "skipped"
            assert job.error == "provider_not_configured"
            entry_id = entry.id
    finally:
        if entry_id:
            with SessionLocal() as db:
                db.execute(delete(AIJob).where(AIJob.entry_id == entry_id))
                db.execute(delete(ContentUnit).where(ContentUnit.entry_id == entry_id))
                db.execute(delete(Entry).where(Entry.id == entry_id))
                db.commit()


def test_entry_multi_classification_edits_search_and_fallback(monkeypatch):
    marker = f"multiclass-{uuid4()}"
    entry_ids: list[UUID] = []
    try:
        monkeypatch.setattr("app.services.entries._enqueue", lambda entry_id: None)
        with TestClient(app) as client:
            headers = _login(client)
            with SessionLocal() as db:
                entry = _make_entry(db, marker)
                legacy = _make_entry(db, f"{marker}-legacy", content_type="decision")
                db.commit()
                entry_ids = [entry.id, legacy.id]

            # Legacy single-type row still returns the primary type in the set.
            legacy_out = client.get(f"/api/v1/entries/{legacy.id}", headers=headers)
            assert legacy_out.status_code == 200, legacy_out.text
            assert legacy_out.json()["content_types"] == ["decision"]

            update = client.patch(
                f"/api/v1/entries/{entry.id}/metadata",
                headers=headers,
                json={"content_types": ["log", "decision"]},
            )
            assert update.status_code == 200, update.text
            body = update.json()
            assert body["content_types"] == ["log", "decision"]
            assert body["content_type"] == "log"
            assert body["content_types_locked"] is True

            detail = client.get(f"/api/v1/entries/{entry.id}", headers=headers)
            assert detail.json()["content_types"] == ["log", "decision"]

            search = client.get(f"/api/v1/search?q={marker}&content_type=decision", headers=headers)
            assert search.status_code == 200, search.text
            assert any(item["entry_id"] == str(entry.id) for item in search.json()["items"])

            empty = client.patch(
                f"/api/v1/entries/{entry.id}/metadata",
                headers=headers,
                json={"content_types": []},
            )
            assert empty.status_code == 422
    finally:
        if entry_ids:
            with SessionLocal() as db:
                db.execute(delete(ContentUnit).where(ContentUnit.entry_id.in_(entry_ids)))
                db.execute(delete(Entry).where(Entry.id.in_(entry_ids)))
                db.commit()


def test_related_entries_return_deterministic_reasons():
    marker = f"related-{uuid4()}"
    entry_ids: list[UUID] = []
    entity_ids: list[UUID] = []
    try:
        with TestClient(app) as client:
            headers = _login(client)
            with SessionLocal() as db:
                first = _make_entry(db, f"{marker}-first")
                second = _make_entry(db, f"{marker}-second")
                entity = Entity(
                    entity_type="host",
                    canonical_name=f"host-{marker}",
                    normalized_name=f"host-{marker}".casefold(),
                )
                db.add(entity)
                db.flush()
                db.add_all(
                    [
                        EntryEntity(
                            entry_id=first.id,
                            entity_id=entity.id,
                            mention_text=f"host-{marker}",
                            source="ai",
                        ),
                        EntryEntity(
                            entry_id=second.id,
                            entity_id=entity.id,
                            mention_text=f"host-{marker}",
                            source="ai",
                        ),
                    ]
                )
                db.commit()
                entry_ids = [first.id, second.id]
                entity_ids = [entity.id]

            response = client.get(f"/api/v1/entries/{entry_ids[0]}/related", headers=headers)
            assert response.status_code == 200, response.text
            payload = response.json()
            assert len(payload) == 1
            assert payload[0]["entry_id"] == str(entry_ids[1])
            assert "共享实体" in payload[0]["reasons"]
            assert payload[0]["score"] > 0

            missing = client.get(f"/api/v1/entries/{uuid4()}/related", headers=headers)
            assert missing.status_code == 404
    finally:
        with SessionLocal() as db:
            db.execute(delete(EntryEntity).where(EntryEntity.entity_id.in_(entity_ids)))
            db.execute(delete(Entity).where(Entity.id.in_(entity_ids)))
            db.execute(delete(ContentUnit).where(ContentUnit.entry_id.in_(entry_ids)))
            db.execute(delete(Entry).where(Entry.id.in_(entry_ids)))
            db.commit()


def test_entry_ai_status_aggregates_latest_jobs():
    marker = f"aistatus-{uuid4()}"
    entry_id: UUID | None = None
    try:
        with TestClient(app) as client:
            headers = _login(client)
            with SessionLocal() as db:
                entry = _make_entry(db, marker)
                db.add_all(
                    [
                        AIJob(
                            entry_id=entry.id,
                            job_type="chunk",
                            status="done",
                            generation=entry.ai_generation,
                        ),
                        AIJob(
                            entry_id=entry.id,
                            job_type="classify",
                            status="failed",
                            error="boom",
                            generation=entry.ai_generation,
                        ),
                    ]
                )
                db.commit()
                entry_id = entry.id

            response = client.get(f"/api/v1/entries/{entry_id}/ai-status", headers=headers)
            assert response.status_code == 200, response.text
            items = {item["job_type"]: item for item in response.json()["items"]}
            assert items["chunk"]["status"] == "done"
            assert items["chunk"]["label"] == "索引"
            assert items["classify"]["status"] == "failed"
            assert items["classify"]["error"] == "boom"
    finally:
        if entry_id:
            with SessionLocal() as db:
                db.execute(delete(AIJob).where(AIJob.entry_id == entry_id))
                db.execute(delete(ContentUnit).where(ContentUnit.entry_id == entry_id))
                db.execute(delete(Entry).where(Entry.id == entry_id))
                db.commit()


def test_memory_lifecycle_expire_filter_and_delete():
    marker = f"memlife-{uuid4()}"
    entry_id: UUID | None = None
    memory_id: UUID | None = None
    try:
        with TestClient(app) as client:
            headers = _login(client)
            with SessionLocal() as db:
                entry = _make_entry(db, marker)
                db.commit()
                entry_id = entry.id

            created = client.post(
                f"/api/v1/entries/{entry_id}/memory-candidates",
                headers=headers,
                json={
                    "subject": f"svc-{marker}",
                    "predicate": "runs_on",
                    "value": f"host-{marker}",
                    "memory_text": f"{marker} runs on host",
                },
            )
            assert created.status_code == 201, created.text
            memory = created.json()["memory"]
            assert memory is not None
            memory_id = memory["id"]

            active = client.get("/api/v1/memories?status=active", headers=headers)
            assert any(item["id"] == memory_id for item in active.json())

            expired = client.post(f"/api/v1/memories/{memory_id}/expire", headers=headers)
            assert expired.status_code == 200, expired.text
            assert expired.json()["status"] == "expired"
            assert expired.json()["expired_at"] is not None

            filtered = client.get("/api/v1/memories?status=expired", headers=headers)
            assert any(item["id"] == memory_id for item in filtered.json())
            active_after = client.get("/api/v1/memories?status=active", headers=headers)
            assert not any(item["id"] == memory_id for item in active_after.json())

            removed = client.delete(f"/api/v1/memories/{memory_id}", headers=headers)
            assert removed.status_code == 204
            with SessionLocal() as db:
                assert db.get(Memory, UUID(memory_id)).status == "deleted"
    finally:
        with SessionLocal() as db:
            if entry_id:
                db.execute(delete(MemoryCandidate).where(MemoryCandidate.entry_id == entry_id))
                db.execute(delete(ContentUnit).where(ContentUnit.entry_id == entry_id))
                db.execute(delete(Entry).where(Entry.id == entry_id))
            if memory_id:
                db.execute(delete(Memory).where(Memory.id == UUID(memory_id)))
            db.commit()


def test_prompt_studio_clone_params_and_test_case_crud():
    created_version_ids: list[UUID] = []
    created_case_ids: list[UUID] = []
    name = "memory_extract"
    try:
        with TestClient(app) as client:
            headers = _login(client)

            clone = client.post(f"/api/v1/prompts/{name}/clone", headers=headers)
            assert clone.status_code == 201, clone.text
            clone_body = clone.json()
            assert clone_body["status"] == "draft"
            assert clone_body["prompt_text"]
            created_version_ids.append(clone_body["id"])

            draft = client.post(
                f"/api/v1/prompts/{name}/draft",
                headers=headers,
                json={
                    "prompt_text": "Updated task prompt for parity closure.",
                    "temperature": 0.25,
                    "top_p": 0.8,
                    "max_tokens": 512,
                    "provider": "openai-compatible",
                    "model": "qwen35-4b",
                },
            )
            assert draft.status_code == 201, draft.text
            draft_body = draft.json()
            assert draft_body["prompt_text"] == "Updated task prompt for parity closure."
            assert draft_body["temperature"] == 0.25
            assert draft_body["top_p"] == 0.8
            assert draft_body["max_tokens"] == 512
            created_version_ids.append(draft_body["id"])

            cases = client.get(f"/api/v1/prompts/{name}/test-cases", headers=headers)
            assert cases.status_code == 200, cases.text
            builtin_case = next(item for item in cases.json() if item["is_builtin"])

            created_case = client.post(
                f"/api/v1/prompts/{name}/test-cases",
                headers=headers,
                json={
                    "name": f"custom-{uuid4()}",
                    "input_json": {"raw_content": "custom input"},
                    "expected_json": {"observation_type": "fact"},
                },
            )
            assert created_case.status_code == 201, created_case.text
            case_id = created_case.json()["id"]
            created_case_ids.append(case_id)
            assert created_case.json()["is_builtin"] is False

            updated_case = client.patch(
                f"/api/v1/prompts/{name}/test-cases/{case_id}",
                headers=headers,
                json={"name": "custom-renamed", "input_json": {"raw_content": "x"}},
            )
            assert updated_case.status_code == 200, updated_case.text
            assert updated_case.json()["name"] == "custom-renamed"

            blocked = client.delete(
                f"/api/v1/prompts/{name}/test-cases/{builtin_case['id']}", headers=headers
            )
            assert blocked.status_code == 409

            removed = client.delete(f"/api/v1/prompts/{name}/test-cases/{case_id}", headers=headers)
            assert removed.status_code == 204
            created_case_ids.remove(case_id)
    finally:
        with SessionLocal() as db:
            if created_case_ids:
                db.execute(
                    delete(PromptTestCase).where(
                        PromptTestCase.id.in_([UUID(item) for item in created_case_ids])
                    )
                )
            if created_version_ids:
                db.execute(
                    delete(PromptVersion).where(
                        PromptVersion.id.in_([UUID(item) for item in created_version_ids])
                    )
                )
            db.commit()


def test_saved_search_persists_and_reuses_filters():
    marker = f"savedfilter-{uuid4()}"
    entry_id: UUID | None = None
    saved_id: UUID | None = None
    try:
        with TestClient(app) as client:
            headers = _login(client)
            with SessionLocal() as db:
                entry = _make_entry(db, marker, content_types=["decision"])
                db.commit()
                entry_id = entry.id

            created = client.post(
                "/api/v1/saved-searches",
                headers=headers,
                json={
                    "name": marker,
                    "query": marker,
                    "source_scope": "native",
                    "filters_json": {"mode": "fulltext", "content_type": "decision"},
                },
            )
            assert created.status_code == 201, created.text
            saved_id = created.json()["id"]
            assert created.json()["filters_json"]["content_type"] == "decision"

            results = client.get(f"/api/v1/saved-searches/{saved_id}/results", headers=headers)
            assert results.status_code == 200, results.text
            assert results.json()["mode"] == "fulltext"
            assert any(item["entry_id"] == str(entry_id) for item in results.json()["items"])
    finally:
        with SessionLocal() as db:
            if saved_id:
                from app.models import SavedSearch

                db.execute(delete(SavedSearch).where(SavedSearch.id == UUID(saved_id)))
            if entry_id:
                db.execute(delete(ContentUnit).where(ContentUnit.entry_id == entry_id))
                db.execute(delete(Entry).where(Entry.id == entry_id))
            db.commit()


def test_clone_does_not_disturb_production_version():
    name = "observation_extract"
    created_version_ids: list[UUID] = []
    try:
        with TestClient(app) as client:
            headers = _login(client)
            before = client.get(f"/api/v1/prompts/{name}", headers=headers)
            production_before = next(
                item for item in before.json()["versions"] if item["status"] == "production"
            )
            clone = client.post(f"/api/v1/prompts/{name}/clone", headers=headers)
            assert clone.status_code == 201, clone.text
            created_version_ids.append(clone.json()["id"])

            after = client.get(f"/api/v1/prompts/{name}", headers=headers)
            production_after = next(
                item for item in after.json()["versions"] if item["status"] == "production"
            )
            assert production_after["id"] == production_before["id"]
            assert production_after["prompt_text"] == production_before["prompt_text"]
    finally:
        with SessionLocal() as db:
            if created_version_ids:
                db.execute(
                    delete(PromptVersion).where(
                        PromptVersion.id.in_([UUID(item) for item in created_version_ids])
                    )
                )
            db.commit()
