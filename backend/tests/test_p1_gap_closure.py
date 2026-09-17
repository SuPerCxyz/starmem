from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.config import get_settings
from app.db import SessionLocal
from app.main import app
from app.models import (
    AIJob,
    AskQuery,
    Attachment,
    ContentUnit,
    Entity,
    Entry,
    EntryEntity,
    EntryVersion,
    IngestionJob,
    Observation,
    Project,
    Relation,
    Source,
    Topic,
)
from app.schemas import SearchResult
from app.services.analytics import frequent_queries, record_query
from app.services.batch import MAX_BATCH_ENTRIES
from app.services.reranking import rerank_results
from app.storage import remove_attachment, write_attachment


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
    entry = Entry(
        source_id=_native_source(db).id,
        title=f"Entry {marker}",
        raw_content=f"{marker}\nfixture content",
        content_type="note",
        **kwargs,
    )
    db.add(entry)
    db.flush()
    db.add(
        EntryVersion(
            entry_id=entry.id,
            version_number=1,
            raw_content=entry.raw_content,
            title=entry.title,
            change_source="user",
        )
    )
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
    return entry


def test_relations_endpoint_returns_outbound_inbound_and_404():
    marker = f"relations-{uuid4()}"
    with TestClient(app) as client:
        headers = _login(client)
        relation_ids: list[UUID] = []
        entry_ids: list[UUID] = []
        try:
            with SessionLocal() as db:
                first = _make_entry(db, f"{marker}-first")
                second = _make_entry(db, f"{marker}-second")
                third = _make_entry(db, f"{marker}-third")
                isolated = _make_entry(db, f"{marker}-isolated")
                relation = Relation(
                    source_type="entry",
                    source_id=first.id,
                    relation_type="relates_to",
                    target_type="entry",
                    target_id=second.id,
                    confidence=0.8,
                    source="ai",
                )
                inbound = Relation(
                    source_type="entry",
                    source_id=third.id,
                    relation_type="supports",
                    target_type="entry",
                    target_id=first.id,
                    confidence=0.6,
                    source="ai",
                )
                db.add_all([relation, inbound])
                db.commit()
                relation_ids = [relation.id, inbound.id]
                entry_ids = [first.id, second.id, third.id, isolated.id]

            response = client.get(f"/api/v1/entries/{entry_ids[0]}/relations", headers=headers)
            assert response.status_code == 200, response.text
            payload = response.json()
            assert {item["direction"] for item in payload} == {"outbound", "inbound"}
            outbound = next(item for item in payload if item["direction"] == "outbound")
            assert outbound["relation_type"] == "relates_to"
            assert outbound["target"]["id"] == str(entry_ids[1])
            assert outbound["confidence"] == 0.8

            empty = client.get(f"/api/v1/entries/{entry_ids[3]}/relations", headers=headers)
            assert empty.status_code == 200
            assert empty.json() == []

            missing = client.get(f"/api/v1/entries/{uuid4()}/relations", headers=headers)
            assert missing.status_code == 404
        finally:
            with SessionLocal() as db:
                db.execute(delete(Relation).where(Relation.id.in_(relation_ids)))
                db.execute(delete(Entry).where(Entry.id.in_(entry_ids)))
                db.commit()


def test_metadata_edit_locks_values_and_survives_ai_reprocessing(monkeypatch):
    marker = f"metadata-{uuid4()}"
    entry_id: UUID | None = None
    project_id: UUID | None = None
    try:
        monkeypatch.setattr("app.services.entries._enqueue", lambda entry_id: None)
        with TestClient(app) as client:
            headers = _login(client)
            with SessionLocal() as db:
                entry = _make_entry(db, marker)
                project = Project(name=f"Project {marker}")
                db.add(project)
                db.commit()
                entry_id = entry.id
                project_id = project.id

            invalid = client.patch(
                f"/api/v1/entries/{entry_id}/metadata",
                headers=headers,
                json={"importance": 101},
            )
            assert invalid.status_code == 422

            unknown = client.patch(
                f"/api/v1/entries/{entry_id}/metadata",
                headers=headers,
                json={"project": f"Missing {marker}"},
            )
            assert unknown.status_code in {404, 422}

            update = client.patch(
                f"/api/v1/entries/{entry_id}/metadata",
                headers=headers,
                json={
                    "content_type": "decision",
                    "summary": f"Summary {marker}",
                    "project": project.name,
                    "importance": 42,
                },
            )
            assert update.status_code == 200, update.text
            body = update.json()
            assert body["content_type"] == "decision"
            assert body["importance"] == 42
            assert body["summary_locked"] is True
            assert body["project_locked"] is True

            reprocessed = client.post(f"/api/v1/entries/{entry_id}/reprocess", headers=headers)
            assert reprocessed.status_code == 200, reprocessed.text

            with SessionLocal() as db:
                locked = db.scalar(
                    select(Observation).where(
                        Observation.entry_id == entry_id,
                        Observation.observation_type == "summary",
                        Observation.is_user_locked.is_(True),
                    )
                )
                assert locked and locked.data_json["summary"] == f"Summary {marker}"

            cleared = client.patch(
                f"/api/v1/entries/{entry_id}/metadata",
                headers=headers,
                json={"summary": None},
            )
            assert cleared.status_code == 200
            assert cleared.json()["summary"] is None
            assert cleared.json()["summary_locked"] is False
    finally:
        if entry_id:
            with SessionLocal() as db:
                db.execute(delete(Entry).where(Entry.id == entry_id))
                if project_id:
                    db.execute(delete(Project).where(Project.id == project_id))
                db.commit()


def test_workbench_management_hides_merged_and_excluded_without_deleting_evidence():
    marker = f"workbench-manage-{uuid4()}"
    entry_id: UUID | None = None
    project_ids: list[UUID] = []
    topic_ids: list[UUID] = []
    entity_ids: list[UUID] = []
    try:
        with TestClient(app) as client:
            headers = _login(client)
            with SessionLocal() as db:
                entry = _make_entry(db, marker)
                source_project = Project(name=f"Merged {marker}")
                target_project = Project(name=f"Target {marker}")
                excluded_topic = Topic(name=f"Excluded {marker}")
                entity = Entity(
                    entity_type="host",
                    canonical_name=f"host-{marker}",
                    normalized_name=f"host-{marker}".casefold(),
                )
                target_entity = Entity(
                    entity_type="host",
                    canonical_name=f"host-target-{marker}",
                    normalized_name=f"host-target-{marker}".casefold(),
                )
                db.add_all([source_project, target_project, excluded_topic, entity, target_entity])
                db.flush()
                entry_id = entry.id
                project_ids = [source_project.id, target_project.id]
                topic_ids = [excluded_topic.id]
                entity_ids = [entity.id, target_entity.id]
                db.add(
                    Observation(
                        entry_id=entry.id,
                        observation_type="project",
                        data_json={"name": source_project.name},
                        source="ai",
                    )
                )
                db.add(
                    EntryEntity(
                        entry_id=entry.id,
                        entity_id=entity.id,
                        mention_text=entity.canonical_name,
                        confidence=1.0,
                        source="ai",
                    )
                )
                db.commit()

            merge = client.post(
                f"/api/v1/projects/{project_ids[0]}/merge",
                headers=headers,
                json={"target_id": str(project_ids[1])},
            )
            assert merge.status_code == 200, merge.text
            assert merge.json()["moved_observations"] == 1

            exclude = client.post(f"/api/v1/topics/{topic_ids[0]}/exclude", headers=headers)
            assert exclude.status_code == 200
            assert exclude.json()["status"] == "excluded"

            rename_conflict = client.patch(
                f"/api/v1/projects/{project_ids[1]}",
                headers=headers,
                json={"name": f"Merged {marker}"},
            )
            assert rename_conflict.status_code == 409

            projects = client.get("/api/v1/projects", headers=headers).json()
            names = {item["name"] for item in projects}
            assert f"Merged {marker}" not in names
            assert f"Target {marker}" in names
            assert all(item["status"] == "active" for item in projects)

            topics = client.get("/api/v1/topics", headers=headers).json()
            assert f"Excluded {marker}" not in {item["name"] for item in topics}

            with SessionLocal() as db:
                repointed = db.scalar(
                    select(Observation).where(
                        Observation.entry_id == entry_id,
                        Observation.observation_type == "project",
                    )
                )
                assert repointed and repointed.data_json["name"] == f"Target {marker}"
                assert db.get(Entry, entry_id) is not None
                assert db.get(Entity, entity_ids[0]) is not None

            entity_merge = client.post(
                f"/api/v1/entities/{entity_ids[0]}/merge",
                headers=headers,
                json={"target_id": str(entity_ids[1])},
            )
            assert entity_merge.status_code == 200, entity_merge.text
            with SessionLocal() as db:
                link = db.get(EntryEntity, (entry_id, entity_ids[1]))
                assert link is not None
                assert db.get(EntryEntity, (entry_id, entity_ids[0])) is None

            entity_missing = client.post(
                f"/api/v1/entities/{entity_ids[1]}/merge",
                headers=headers,
                json={"target_id": str(uuid4())},
            )
            assert entity_missing.status_code == 404
    finally:
        with SessionLocal() as db:
            if entry_id:
                db.execute(delete(Entry).where(Entry.id == entry_id))
            if project_ids:
                db.execute(delete(Project).where(Project.id.in_(project_ids)))
            if topic_ids:
                db.execute(delete(Topic).where(Topic.id.in_(topic_ids)))
            if entity_ids:
                db.execute(delete(Entity).where(Entity.id.in_(entity_ids)))
            db.commit()


def test_inbox_correction_appends_version_and_rejects_processing(monkeypatch):
    marker = f"inbox-fix-{uuid4()}"
    entry_id: UUID | None = None
    job_id: UUID | None = None
    try:
        with SessionLocal() as db:
            entry = _make_entry(db, marker)
            job = IngestionJob(
                entry_id=entry.id,
                input_kind="file",
                source_id=_native_source(db).id,
                status="processed",
                original_name="original.txt",
                media_type="text/plain",
            )
            db.add(job)
            db.commit()
            entry_id = entry.id
            job_id = job.id

        with TestClient(app) as client:
            headers = _login(client)
            corrected = client.patch(
                f"/api/v1/inbox/{job_id}",
                headers=headers,
                json={"title": f"Corrected {marker}", "content_type": "log"},
            )
            assert corrected.status_code == 200, corrected.text
            assert corrected.json()["metadata_json"]["user_corrected"] is True

            with SessionLocal() as db:
                entry = db.get(Entry, entry_id)
                assert entry.title == f"Corrected {marker}"
                assert entry.content_type == "log"
                versions = db.scalars(
                    select(EntryVersion)
                    .where(EntryVersion.entry_id == entry_id)
                    .order_by(EntryVersion.version_number)
                ).all()
                assert [version.version_number for version in versions] == [1, 2]

            with SessionLocal() as db:
                job = db.get(IngestionJob, job_id)
                job.status = "processing"
                db.commit()
            conflict = client.patch(
                f"/api/v1/inbox/{job_id}",
                headers=headers,
                json={"title": "should not apply"},
            )
            assert conflict.status_code == 409

            missing = client.patch(
                f"/api/v1/inbox/{uuid4()}",
                headers=headers,
                json={"title": "missing"},
            )
            assert missing.status_code == 404
    finally:
        if entry_id:
            with SessionLocal() as db:
                db.execute(delete(IngestionJob).where(IngestionJob.entry_id == entry_id))
                db.execute(delete(Entry).where(Entry.id == entry_id))
                db.commit()


def test_batch_reprocess_limits_and_reports_counts(monkeypatch):
    marker = f"batch-{uuid4()}"
    entry_ids: list[UUID] = []
    try:
        monkeypatch.setattr("app.services.entries._enqueue", lambda entry_id: None)
        with SessionLocal() as db:
            entries = [_make_entry(db, f"{marker}-{index}") for index in range(2)]
            db.commit()
            entry_ids = [entry.id for entry in entries]

        with TestClient(app) as client:
            headers = _login(client)
            success = client.post(
                "/api/v1/entries/reprocess-batch",
                headers=headers,
                json={"entry_ids": [str(entry_id) for entry_id in entry_ids]},
            )
            assert success.status_code == 200, success.text
            assert success.json()["submitted_count"] == 2
            assert success.json()["failed_count"] == 0

            unknown = client.post(
                "/api/v1/entries/reprocess-batch",
                headers=headers,
                json={"entry_ids": [str(uuid4())]},
            )
            assert unknown.status_code == 422

            oversized = client.post(
                "/api/v1/entries/reprocess-batch",
                headers=headers,
                json={"entry_ids": [str(uuid4()) for _ in range(MAX_BATCH_ENTRIES + 1)]},
            )
            assert oversized.status_code == 422
    finally:
        with SessionLocal() as db:
            db.execute(delete(Entry).where(Entry.id.in_(entry_ids)))
            db.commit()


def test_image_description_metadata_reports_skip_reason(monkeypatch):
    marker = f"image-{uuid4()}"
    entry_id: UUID | None = None
    storage_key: str | None = None
    try:
        monkeypatch.setattr("app.services.entries._enqueue", lambda entry_id: None)
        from app.worker import _run_image_description_job

        with SessionLocal() as db:
            entry = _make_entry(db, marker)
            entry_id = entry.id
            storage_key, digest = write_attachment(b"\x89PNG fake", "photo.png")
            db.add(
                Attachment(
                    entry_id=entry.id,
                    storage_key=storage_key,
                    original_filename="photo.png",
                    media_type="image/png",
                    size_bytes=10,
                    content_hash=digest,
                    processing_status="processed",
                )
            )
            db.add(AIJob(entry_id=entry.id, job_type="image_describe", generation=0))
            db.commit()
            _run_image_description_job(db, entry, 0)
            job = db.scalar(
                select(AIJob).where(AIJob.entry_id == entry.id, AIJob.job_type == "image_describe")
            )
            assert job.status == "skipped"
            assert job.error == "image_description_disabled"

        with TestClient(app) as client:
            headers = _login(client)
            metadata = client.get(f"/api/v1/entries/{entry_id}/metadata", headers=headers)
            assert metadata.status_code == 200, metadata.text
            assert metadata.json()["image_description"] is None
            assert metadata.json()["image_description_status"] == "skipped"
            assert metadata.json()["image_description_detail"] == "image_description_disabled"
    finally:
        if storage_key:
            remove_attachment(storage_key)
        if entry_id:
            with SessionLocal() as db:
                db.execute(delete(Entry).where(Entry.id == entry_id))
                db.commit()


def test_reranker_success_and_fallback(monkeypatch):
    from app.services import reranking

    def _item(score: float, snippet: str) -> SearchResult:
        return SearchResult(
            entry_id=uuid4(),
            content_unit_id=uuid4(),
            source_id=uuid4(),
            source_name="Fixture",
            source_type="native",
            created_at=None,
            snippet=snippet,
            score=score,
            match_reason="Hybrid",
            exact_match=False,
        )

    items = [_item(0.9, "first"), _item(0.3, "second")]

    class _Response:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    monkeypatch.setattr(
        reranking,
        "get_settings",
        lambda: type(
            "S",
            (),
            {
                "reranker_provider": "http",
                "reranker_base_url": "http://reranker.local",
                "reranker_model": "bge-reranker",
                "reranker_timeout_seconds": 5,
            },
        )(),
    )
    monkeypatch.setattr(
        reranking.httpx,
        "post",
        lambda *args, **kwargs: _Response(
            {
                "results": [
                    {"index": 1, "relevance_score": 0.99},
                    {"index": 0, "relevance_score": 0.1},
                ]
            }
        ),
    )
    ranked = rerank_results("query", items)
    assert ranked[0].snippet == "second"
    assert ranked[0].match_reason == "Hybrid + Rerank"

    def _boom(*args, **kwargs):
        raise reranking.httpx.ConnectError("unreachable")

    monkeypatch.setattr(reranking.httpx, "post", _boom)
    fallback = rerank_results("query", items)
    assert [item.snippet for item in fallback] == ["first", "second"]
    assert fallback[0].match_reason == "Hybrid"

    monkeypatch.setattr(
        reranking.httpx,
        "post",
        lambda *args, **kwargs: _Response({"results": [{"index": 0, "score": 0.5}]}),
    )
    mismatched = rerank_results("query", items)
    assert [item.snippet for item in mismatched] == ["first", "second"]


def test_ask_analytics_redacts_aggregates_and_smart_view():
    marker = f"ask-{uuid4()}"
    entry_id: UUID | None = None
    try:
        with SessionLocal() as db:
            record_query(
                db,
                query=f"{marker} password=not-a-real-secret",
                source_scope="all",
                result_count=1,
                latency_ms=12,
            )
            record_query(
                db,
                query=f"{marker} password=not-a-real-secret",
                source_scope="all",
                result_count=2,
                latency_ms=20,
            )
            stored = db.scalars(
                select(AskQuery).where(AskQuery.query_text.like(f"%{marker}%"))
            ).all()
            assert stored and len(stored) == 2
            assert all("not-a-real-secret" not in row.query_text for row in stored)
            assert all("REDACTED" in row.query_text for row in stored)

            aggregated = frequent_queries(db, limit=10)
            matching = [item for item in aggregated if marker in item.title]
            assert len(matching) == 1
            assert matching[0].status == "2"

        with TestClient(app) as client:
            headers = _login(client)
            created = client.post(
                "/api/v1/entries",
                headers=headers,
                json={"raw_content": f"{marker} analytics fixture"},
            )
            assert created.status_code == 201, created.text
            entry_id = UUID(created.json()["id"])
            asked = client.post(
                "/api/v1/ask", headers=headers, json={"query": f"{marker} 是什么？"}
            )
            assert asked.status_code == 200, asked.text

            definitions = client.get("/api/v1/smart-views", headers=headers).json()
            assert any(item["id"] == "ask-frequent" for item in definitions)
            view = client.get("/api/v1/smart-views/ask-frequent", headers=headers)
            assert view.status_code == 200
            assert view.json()["items"]
    finally:
        with SessionLocal() as db:
            db.execute(delete(AskQuery).where(AskQuery.query_text.like(f"%{marker}%")))
            if entry_id:
                db.execute(delete(Entry).where(Entry.id == entry_id))
            db.commit()
