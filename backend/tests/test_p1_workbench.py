from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

import app.ai_tasks as ai_tasks_module
from app.ai_tasks import _run_chat
from app.config import get_settings
from app.db import SessionLocal
from app.main import app
from app.models import (
    AIJob,
    ContentUnit,
    Entity,
    Entry,
    EntryEntity,
    Knowledge,
    Memory,
    Observation,
    Project,
    SavedSearch,
    Topic,
    UserSetting,
)
from app.providers import ChatResult
from app.routing import task_route
from app.secret_scanner import scan_secrets


def _login(client: TestClient) -> dict[str, str]:
    settings = get_settings()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
    )
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def test_secret_scan_returns_only_safe_location_summaries():
    raw = "password=not-a-real-secret\nAuthorization: Bearer not-a-real-token\n"
    findings = scan_secrets(raw)
    assert {item["type"] for item in findings} >= {"credential", "authorization"}
    assert all(set(item) == {"type", "line", "column"} for item in findings)
    assert all("not-a-real" not in str(item) for item in findings)


def test_workbench_safety_similarity_views_saved_search_review_and_knowledge():
    marker = f"workbench-{uuid4()}"
    project_name = f"Project {marker}"
    topic_name = f"Topic {marker}"
    entry_ids: list[UUID] = []
    memory_id: UUID | None = None
    project_id: UUID | None = None
    topic_id: UUID | None = None
    entity_id: UUID | None = None
    knowledge_id: UUID | None = None
    saved_search_id: UUID | None = None
    settings_before: dict[str, object] | None = None
    try:
        with SessionLocal() as db:
            source = db.scalar(select(Entry.source_id).limit(1))
            if source is None:
                from app.models import Source

                source_row = db.scalar(select(Source).where(Source.is_native.is_(True)))
                assert source_row
                source = source_row.id
            project = Project(name=project_name, description="Workbench fixture")
            topic = Topic(name=topic_name)
            entity = Entity(
                entity_type="service",
                canonical_name=f"service-{marker}",
                normalized_name=f"service-{marker}".casefold(),
            )
            db.add_all([project, topic, entity])
            db.flush()
            project_id, topic_id, entity_id = project.id, topic.id, entity.id
            first = Entry(
                source_id=source,
                title=f"Problem {marker}",
                raw_content=(
                    f"{marker}\n故障：service unavailable\n"
                    "password=not-a-real-secret\nTODO: confirm recovery"
                ),
                content_type="troubleshooting",
            )
            second = Entry(
                source_id=source,
                title=f"Decision {marker}",
                raw_content=f"{marker}\n最终方案：决定固定 service rollout；测试性能已完成。",
                content_type="decision",
            )
            db.add_all([first, second])
            db.flush()
            entry_ids = [first.id, second.id]
            db.add_all(
                [
                    ContentUnit(
                        owner_type="entry",
                        owner_id=entry.id,
                        source_id=source,
                        entry_id=entry.id,
                        unit_type="entry",
                        content=entry.raw_content,
                    )
                    for entry in (first, second)
                ]
            )
            db.add_all(
                [
                    EntryEntity(
                        entry_id=first.id,
                        entity_id=entity.id,
                        mention_text=entity.canonical_name,
                        confidence=1.0,
                        source="user",
                    ),
                    Observation(
                        entry_id=first.id,
                        observation_type="project",
                        data_json={"name": project.name},
                        source="user",
                    ),
                    Observation(
                        entry_id=first.id,
                        observation_type="topic",
                        data_json={"name": topic.name},
                        source="user",
                    ),
                    Memory(
                        subject_key=f"service-{marker}",
                        predicate="availability",
                        scope_key=f"service-{marker}:availability",
                        value_json={"value": "restored"},
                        value_key="restored",
                        memory_text=f"{marker} service was restored",
                        status="active",
                        source_entry_id=first.id,
                        confidence=0.95,
                    ),
                    AIJob(
                        entry_id=first.id,
                        job_type="summary",
                        status="failed",
                        generation=0,
                        error="fixture failure",
                    ),
                ]
            )
            db.flush()
            memory_id = db.scalar(select(Memory.id).where(Memory.source_entry_id == first.id))
            settings_row = db.scalar(select(UserSetting).order_by(UserSetting.updated_at.desc()))
            assert settings_row
            settings_before = dict(settings_row.model_routing or {})
            db.commit()

        with TestClient(app) as client:
            headers = _login(client)
            safety = client.get(f"/api/v1/entries/{entry_ids[0]}/safety")
            assert safety.status_code == 200, safety.text
            safety_payload = safety.json()
            assert safety_payload["detected"] is True
            assert any(item["type"] == "credential" for item in safety_payload["findings"])
            assert "not-a-real-secret" not in safety.text

            rescanned = client.post(
                f"/api/v1/entries/{entry_ids[0]}/safety/rescan", headers=headers
            )
            assert rescanned.status_code == 200, rescanned.text
            similar = client.get(f"/api/v1/entries/{entry_ids[0]}/similar")
            assert similar.status_code == 200, similar.text
            assert all(item["entry_id"] != str(entry_ids[0]) for item in similar.json())

            projects = client.get("/api/v1/projects")
            assert projects.status_code == 200, projects.text
            project_summary = next(
                item for item in projects.json() if item["id"] == str(project_id)
            )
            assert project_summary["entry_count"] == 1
            assert project_summary["memory_count"] == 1
            assert str(entry_ids[0]) in project_summary["entry_ids"]
            assert client.get(f"/api/v1/projects/{project_id}").json()["name"] == project_name

            topics = client.get("/api/v1/topics")
            assert any(
                item["id"] == str(topic_id) and item["entry_count"] == 1 for item in topics.json()
            )
            entities = client.get("/api/v1/entities")
            assert any(
                item["id"] == str(entity_id) and item["entry_count"] == 1
                for item in entities.json()
            )

            review = client.get("/api/v1/reviews", params={"period": "today"})
            assert review.status_code == 200, review.text
            assert review.json()["counts"]["entries"] >= 2
            assert review.json()["counts"]["problems"] >= 1
            assert review.json()["counts"]["failed_ai_jobs"] >= 1

            failed_view = client.get("/api/v1/smart-views/ai-failed")
            assert failed_view.status_code == 200, failed_view.text
            assert any(item["job_id"] for item in failed_view.json()["items"])
            assert any(
                item["id"] == "conflicted-memory"
                for item in client.get("/api/v1/smart-views").json()
            )

            saved = client.post(
                "/api/v1/saved-searches",
                headers=headers,
                json={
                    "name": f"Saved {marker}",
                    "query": marker,
                    "source_scope": "native",
                    "filters_json": {"content_type": "troubleshooting", "mode": "fulltext"},
                },
            )
            assert saved.status_code == 201, saved.text
            saved_search_id = UUID(saved.json()["id"])
            result = client.get(f"/api/v1/saved-searches/{saved_search_id}/results")
            assert result.status_code == 200, result.text
            assert any(item["entry_id"] == str(entry_ids[0]) for item in result.json()["items"])
            updated = client.patch(
                f"/api/v1/saved-searches/{saved_search_id}",
                headers=headers,
                json={"name": f"Renamed {marker}"},
            )
            assert updated.status_code == 200, updated.text
            assert (
                client.delete(
                    f"/api/v1/saved-searches/{saved_search_id}", headers=headers
                ).status_code
                == 204
            )

            summary = client.post(
                "/api/v1/knowledge/summaries",
                headers=headers,
                json={"scope_type": "project", "scope_value": project_name},
            )
            assert summary.status_code == 201, summary.text
            knowledge_id = UUID(summary.json()["id"])
            assert summary.json()["status"] == "derived"
            assert str(entry_ids[0]) in summary.json()["metadata_json"]["entry_ids"]
            assert str(memory_id) in summary.json()["metadata_json"]["memory_ids"]
            regenerated = client.post(
                "/api/v1/knowledge/summaries",
                headers=headers,
                json={"scope_type": "project", "scope_value": project_name},
            )
            assert regenerated.status_code == 201
            assert regenerated.json()["id"] == str(knowledge_id)

            settings_response = client.patch(
                "/api/v1/settings",
                headers=headers,
                json={
                    "model_routing": {
                        "summary": {"provider": "openai-compatible", "model": "routed-test"}
                    }
                },
            )
            assert settings_response.status_code == 200, settings_response.text
            assert settings_response.json()["model_routing"]["summary"]["model"] == "routed-test"
            assert "api_key" not in settings_response.text.lower()
            invalid_route = client.patch(
                "/api/v1/settings",
                headers=headers,
                json={
                    "model_routing": {"summary": {"provider": "x", "model": "m", "api_key": "bad"}}
                },
            )
            assert invalid_route.status_code == 422

        with SessionLocal() as db:
            prompt = SimpleNamespace(created_by="system", provider=None, model=None)
            assert task_route(db, "summary", prompt) == ("openai-compatible", "routed-test")
            custom = SimpleNamespace(created_by="user", provider="custom", model="custom-model")
            assert task_route(db, "summary", custom) == ("custom", "custom-model")

            class RoutedProvider:
                name = "routed-provider"
                model = "routed-model"

                def complete(self, messages, **kwargs):
                    return ChatResult(
                        content='{"summary":"routed","confidence":0.8,"is_inference":false}',
                        model=self.model,
                    )

            captured: dict[str, str | None] = {}

            def get_routed_provider(**kwargs):
                captured.update(kwargs)
                return RoutedProvider()

            original_get_provider = ai_tasks_module.get_chat_provider
            ai_tasks_module.get_chat_provider = get_routed_provider
            try:
                entry = db.get(Entry, entry_ids[0])
                assert entry
                output = _run_chat(db, entry, "summary", None)
                assert output[0].summary == "routed"
                assert captured == {
                    "model_override": "routed-test",
                    "provider_override": "openai-compatible",
                }
            finally:
                ai_tasks_module.get_chat_provider = original_get_provider
    finally:
        with SessionLocal() as db:
            if settings_before is not None:
                settings_row = db.scalar(
                    select(UserSetting).order_by(UserSetting.updated_at.desc())
                )
                if settings_row:
                    settings_row.model_routing = settings_before
            if saved_search_id:
                db.execute(delete(SavedSearch).where(SavedSearch.id == saved_search_id))
            if knowledge_id:
                db.execute(delete(Knowledge).where(Knowledge.id == knowledge_id))
            if memory_id:
                db.execute(delete(Memory).where(Memory.id == memory_id))
            if entry_ids:
                db.execute(delete(Entry).where(Entry.id.in_(entry_ids)))
            if project_id:
                db.execute(delete(Project).where(Project.id == project_id))
            if topic_id:
                db.execute(delete(Topic).where(Topic.id == topic_id))
            if entity_id:
                db.execute(delete(Entity).where(Entity.id == entity_id))
            db.commit()
