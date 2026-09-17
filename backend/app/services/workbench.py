"""Bounded, explainable queries for the P1 knowledge workbench."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import (
    AIJob,
    Entity,
    Entry,
    EntryEntity,
    Knowledge,
    Memory,
    MemorySource,
    Observation,
    Project,
    Source,
    Topic,
)
from app.schemas import (
    KnowledgeSummaryInput,
    ReviewOut,
    SavedSearchInput,
    SimilarEntryOut,
    SmartViewOut,
    WorkbenchItemOut,
    WorkbenchSummaryOut,
)
from app.secret_scanner import redact_secrets
from app.services.analytics import frequent_queries
from app.services.search import SearchOutcome
from app.services.search import search as search_service

SOURCE_SCOPES = {"all", "native", "external"}
WORKBENCH_KINDS = {"project", "topic", "entity"}
MAX_VISIBLE_ENTRIES = 5_000
MAX_WORKBENCH_ITEMS = 100
MAX_SOURCE_IDS = 250

SAVED_FILTER_KEYS = {
    "start",
    "end",
    "content_type",
    "tag",
    "entity",
    "project",
    "topic",
    "source_id",
    "mode",
}

SMART_VIEW_DEFINITIONS: tuple[tuple[str, str, str], ...] = (
    ("problems", "问题", "需要排查、失败或报错的记录"),
    ("solutions", "解决方案", "包含解决、修复或最终处理结果的记录"),
    ("todo", "待办", "包含 TODO、待办或后续行动的记录"),
    ("decisions", "决策", "明确记录的决定、取舍和固定方案"),
    ("tests-performance", "测试 / 性能", "测试、基准和性能观察记录"),
    ("recent-changes", "最近修改", "最近三十天新增或更新的记录"),
    ("unresolved-issues", "未解决问题", "仍标记为待处理或未解决的问题"),
    ("new-memory", "新增 Memory", "最近三十天新增的 Active Memory"),
    ("conflicted-memory", "冲突 Memory", "当前处于 Conflicted 状态的 Memory"),
    ("ai-failed", "AI 处理失败", "需要重处理的 AI Job 及其 Entry"),
    ("ask-frequent", "最近常问", "最近三十天高频脱敏查询"),
)


def validate_source_scope(source_scope: str) -> str:
    if source_scope not in SOURCE_SCOPES:
        raise ValueError("Unsupported source scope")
    return source_scope


def _visible_entries(
    db: Session,
    *,
    source_scope: str = "all",
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[Entry]:
    validate_source_scope(source_scope)
    statement = (
        select(Entry).join(Source, Source.id == Entry.source_id).where(Entry.deleted_at.is_(None))
    )
    if source_scope == "native":
        statement = statement.where(Source.is_native.is_(True))
    elif source_scope == "external":
        statement = statement.where(Source.is_native.is_(False))
    if start:
        statement = statement.where(Entry.created_at >= start)
    if end:
        statement = statement.where(Entry.created_at <= end)
    statement = statement.order_by(desc(Entry.created_at), desc(Entry.id)).limit(
        MAX_VISIBLE_ENTRIES
    )
    return db.scalars(statement).all()


def _observation_name(observation: Observation) -> str | None:
    data = observation.data_json or {}
    for key in ("name", "project", "topic", "value"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _memory_ids_for_entries(db: Session, entry_ids: set[UUID]) -> list[UUID]:
    if not entry_ids:
        return []
    direct = set(
        db.scalars(
            select(Memory.id).where(
                Memory.status == "active", Memory.source_entry_id.in_(entry_ids)
            )
        ).all()
    )
    linked = set(
        db.scalars(
            select(MemorySource.memory_id)
            .join(Memory, Memory.id == MemorySource.memory_id)
            .where(Memory.status == "active", MemorySource.entry_id.in_(entry_ids))
        ).all()
    )
    return sorted(direct | linked, key=str)


def _related_names(
    db: Session,
    *,
    kind: str,
    item_id: UUID,
    entry_ids: set[UUID],
) -> list[str]:
    names: dict[str, int] = {}
    if kind == "entity":
        links = db.execute(
            select(Entity.id, Entity.canonical_name)
            .join(EntryEntity, EntryEntity.entity_id == Entity.id)
            .where(EntryEntity.entry_id.in_(entry_ids), Entity.id != item_id)
        ).all()
        for _, name in links:
            names[name] = names.get(name, 0) + 1
    else:
        observation_type = kind
        observations = db.scalars(
            select(Observation).where(
                Observation.entry_id.in_(entry_ids),
                Observation.observation_type == observation_type,
            )
        ).all()
        for observation in observations:
            name = _observation_name(observation)
            if name:
                names[name] = names.get(name, 0) + 1
        entity_rows = db.execute(
            select(Entity.canonical_name)
            .join(EntryEntity, EntryEntity.entity_id == Entity.id)
            .where(EntryEntity.entry_id.in_(entry_ids))
        ).all()
        for (name,) in entity_rows:
            names[name] = names.get(name, 0) + 1
    return [name for name, _ in sorted(names.items(), key=lambda item: (-item[1], item[0]))[:8]]


def _summary(
    db: Session,
    *,
    kind: str,
    item: Project | Topic | Entity,
    entries: list[Entry],
) -> WorkbenchSummaryOut:
    entry_ids = {entry.id for entry in entries}
    memory_ids = _memory_ids_for_entries(db, entry_ids)
    ordered = sorted(entries, key=lambda entry: (entry.created_at, str(entry.id)))
    return WorkbenchSummaryOut(
        id=item.id,
        name=item.name if isinstance(item, (Project, Topic)) else item.canonical_name,
        kind=kind,
        status=getattr(item, "status", "active"),
        entity_type=item.entity_type if isinstance(item, Entity) else None,
        description=getattr(item, "description", None),
        first_seen=ordered[0].created_at if ordered else None,
        last_seen=ordered[-1].created_at if ordered else None,
        entry_count=len(entry_ids),
        memory_count=len(memory_ids),
        entry_ids=sorted(entry_ids, key=str)[:MAX_SOURCE_IDS],
        memory_ids=memory_ids[:MAX_SOURCE_IDS],
        related=_related_names(db, kind=kind, item_id=item.id, entry_ids=entry_ids)
        if entry_ids
        else [],
    )


def _entries_for_named_observation(
    db: Session,
    *,
    observation_type: str,
    name: str,
    source_scope: str,
) -> list[Entry]:
    visible = _visible_entries(db, source_scope=source_scope)
    visible_by_id = {entry.id: entry for entry in visible}
    matches = db.scalars(
        select(Observation).where(Observation.observation_type == observation_type)
    ).all()
    target = name.casefold()
    return [
        visible_by_id[observation.entry_id]
        for observation in matches
        if observation.entry_id in visible_by_id
        and (_observation_name(observation) or "").casefold() == target
    ]


def workbench_summary(
    db: Session,
    *,
    kind: str,
    item_id: UUID,
    source_scope: str = "all",
) -> WorkbenchSummaryOut:
    validate_source_scope(source_scope)
    if kind == "project":
        item = db.get(Project, item_id)
        if not item:
            raise ValueError("Project not found")
        entries = _entries_for_named_observation(
            db, observation_type="project", name=item.name, source_scope=source_scope
        )
    elif kind == "topic":
        item = db.get(Topic, item_id)
        if not item:
            raise ValueError("Topic not found")
        entries = _entries_for_named_observation(
            db, observation_type="topic", name=item.name, source_scope=source_scope
        )
    elif kind == "entity":
        item = db.get(Entity, item_id)
        if not item:
            raise ValueError("Entity not found")
        visible = {entry.id: entry for entry in _visible_entries(db, source_scope=source_scope)}
        entry_ids = db.scalars(
            select(EntryEntity.entry_id).where(EntryEntity.entity_id == item_id)
        ).all()
        entries = [visible[entry_id] for entry_id in entry_ids if entry_id in visible]
    else:
        raise ValueError("Unsupported workbench kind")
    return _summary(db, kind=kind, item=item, entries=entries)


def list_workbench(
    db: Session,
    *,
    kind: str,
    source_scope: str = "all",
    limit: int = 100,
) -> list[WorkbenchSummaryOut]:
    validate_source_scope(source_scope)
    if kind == "project":
        items: list[Project | Topic | Entity] = db.scalars(
            select(Project)
            .where(Project.status == "active")
            .order_by(Project.name)
            .limit(min(limit, MAX_WORKBENCH_ITEMS))
        ).all()
    elif kind == "topic":
        items = db.scalars(
            select(Topic)
            .where(Topic.status == "active")
            .order_by(Topic.name)
            .limit(min(limit, MAX_WORKBENCH_ITEMS))
        ).all()
    elif kind == "entity":
        items = db.scalars(
            select(Entity)
            .where(Entity.status == "active")
            .order_by(Entity.entity_type, Entity.canonical_name)
            .limit(min(limit, MAX_WORKBENCH_ITEMS))
        ).all()
    else:
        raise ValueError("Unsupported workbench kind")
    return [
        workbench_summary(db, kind=kind, item_id=item.id, source_scope=source_scope)
        for item in items
    ]


def _entry_title(entry: Entry) -> str:
    if entry.title and entry.title.strip():
        return entry.title.strip()[:160]
    first_line = next((line.strip() for line in entry.raw_content.splitlines() if line.strip()), "")
    return (first_line or "未命名记录")[:160]


def _entry_item(
    entry: Entry, *, kind: str = "entry", detail: str | None = None
) -> WorkbenchItemOut:
    return WorkbenchItemOut(
        id=entry.id,
        kind=kind,
        title=_entry_title(entry),
        entry_id=entry.id,
        status=entry.ai_status,
        detail=detail or entry.raw_content.replace("\n", " ")[:240],
        created_at=entry.created_at,
    )


def _memory_item(memory: Memory, *, kind: str) -> WorkbenchItemOut:
    return WorkbenchItemOut(
        id=memory.id,
        kind=kind,
        title=memory.memory_text[:160],
        entry_id=memory.source_entry_id,
        memory_id=memory.id,
        status=memory.status,
        detail=f"{memory.subject_key} · {memory.predicate}",
        created_at=memory.created_at,
    )


def _failed_job_items(db: Session, *, limit: int = MAX_WORKBENCH_ITEMS) -> list[WorkbenchItemOut]:
    rows = db.execute(
        select(AIJob, Entry)
        .join(Entry, Entry.id == AIJob.entry_id)
        .where(
            Entry.deleted_at.is_(None),
            AIJob.status.in_(("failed", "retrying", "prompt_validation_failed")),
        )
        .order_by(desc(AIJob.created_at))
        .limit(limit)
    ).all()
    return [
        WorkbenchItemOut(
            id=job.id,
            kind="ai-job",
            title=f"{job.job_type} · {_entry_title(entry)}",
            entry_id=entry.id,
            job_id=job.id,
            status=job.status,
            detail=job.error,
            created_at=job.created_at,
        )
        for job, entry in rows
    ]


def _matches_entry(entry: Entry, view_id: str) -> bool:
    content = entry.raw_content.casefold()
    content_type = (entry.content_type or "").casefold()
    if view_id == "problems":
        return content_type in {"troubleshooting", "problem", "incident"} or any(
            term in content for term in ("故障", "报错", "异常", "失败", "error", "exception")
        )
    if view_id == "solutions":
        return content_type in {"solution", "resolution"} or any(
            term in content
            for term in ("解决", "修复", "处理结果", "fixed", "resolved", "solution")
        )
    if view_id == "todo":
        return content_type in {"todo", "task"} or bool(
            re.search(r"(?im)(?:^|\s)(?:todo|待办|下一步|action item|follow[- ]?up)\b", content)
        )
    if view_id == "decisions":
        return content_type == "decision" or any(
            term in content for term in ("决定", "决策", "最终方案", "固定", "decision")
        )
    if view_id == "tests-performance":
        return content_type in {"test", "performance", "benchmark"} or any(
            term in content
            for term in ("测试", "基准", "性能", "benchmark", "latency", "throughput")
        )
    if view_id == "unresolved-issues":
        return _matches_entry(entry, "problems") and any(
            term in content for term in ("未解决", "待处理", "unresolved", "open issue", "todo")
        )
    return False


def run_smart_view(db: Session, view_id: str) -> SmartViewOut:
    definition = next((item for item in SMART_VIEW_DEFINITIONS if item[0] == view_id), None)
    if not definition:
        raise ValueError("Smart View not found")
    now = datetime.now(UTC)
    if view_id in {"new-memory", "conflicted-memory"}:
        statement = select(Memory)
        if view_id == "new-memory":
            statement = statement.where(
                Memory.status == "active", Memory.created_at >= now - timedelta(days=30)
            )
        else:
            statement = statement.where(Memory.status == "conflicted")
        statement = statement.order_by(desc(Memory.updated_at)).limit(MAX_WORKBENCH_ITEMS)
        items = [_memory_item(memory, kind=view_id) for memory in db.scalars(statement).all()]
    elif view_id == "ai-failed":
        items = _failed_job_items(db)
    elif view_id == "ask-frequent":
        items = frequent_queries(db, limit=MAX_WORKBENCH_ITEMS)
    else:
        entries = _visible_entries(db)
        if view_id == "recent-changes":
            cutoff = now - timedelta(days=30)
            entries = [
                entry
                for entry in entries
                if (entry.updated_at and entry.updated_at >= cutoff)
                or (entry.created_at and entry.created_at >= cutoff)
            ]
        else:
            entries = [entry for entry in entries if _matches_entry(entry, view_id)]
        items = [_entry_item(entry, kind=view_id) for entry in entries[:MAX_WORKBENCH_ITEMS]]
    return SmartViewOut(
        id=definition[0], name=definition[1], description=definition[2], items=items
    )


def smart_view_definitions() -> list[SmartViewOut]:
    return [
        SmartViewOut(id=view_id, name=name, description=description, items=[])
        for view_id, name, description in SMART_VIEW_DEFINITIONS
    ]


def validate_saved_filters(filters: dict[str, object]) -> dict[str, object]:
    if len(filters) > len(SAVED_FILTER_KEYS):
        raise ValueError("Too many saved search filters")
    normalized: dict[str, object] = {}
    for key, value in filters.items():
        if key not in SAVED_FILTER_KEYS:
            raise ValueError(f"Unsupported saved search filter: {key}")
        if key in {"start", "end"}:
            if not isinstance(value, str) or len(value) > 80:
                raise ValueError(f"Invalid saved search date: {key}")
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError(f"Invalid saved search date: {key}") from exc
            normalized[key] = value
        elif key == "source_id":
            try:
                normalized[key] = str(UUID(str(value)))
            except (ValueError, AttributeError) as exc:
                raise ValueError("Invalid saved search source_id") from exc
        elif key == "mode":
            if value not in {"hybrid", "fulltext", "semantic"}:
                raise ValueError("Unsupported saved search mode")
            normalized[key] = value
        else:
            if not isinstance(value, str) or not value.strip() or len(value) > 500:
                raise ValueError(f"Invalid saved search filter: {key}")
            normalized[key] = value.strip()
    return normalized


def saved_search_input(payload: SavedSearchInput) -> dict[str, object]:
    source_scope = validate_source_scope(payload.source_scope)
    name = " ".join(payload.name.strip().split())
    query = payload.query.strip()
    if not name or not query:
        raise ValueError("Saved search name and query cannot be blank")
    return {
        "name": name,
        "query": query,
        "source_scope": source_scope,
        "filters_json": validate_saved_filters(payload.filters_json),
    }


def saved_search_results(db: Session, saved_search, *, limit: int = 100) -> SearchOutcome:
    filters = validate_saved_filters(saved_search.filters_json or {})
    source_id = UUID(str(filters["source_id"])) if filters.get("source_id") else None
    parsed_start = (
        datetime.fromisoformat(str(filters["start"]).replace("Z", "+00:00"))
        if filters.get("start")
        else None
    )
    parsed_end = (
        datetime.fromisoformat(str(filters["end"]).replace("Z", "+00:00"))
        if filters.get("end")
        else None
    )
    return search_service(
        db,
        saved_search.query,
        mode=str(filters.get("mode", "hybrid")),
        limit=min(limit, 100),
        source_scope=saved_search.source_scope,
        source_id=source_id,
        start=parsed_start,
        end=parsed_end,
        content_type=str(filters["content_type"]) if filters.get("content_type") else None,
        tag=str(filters["tag"]) if filters.get("tag") else None,
        entity=str(filters["entity"]) if filters.get("entity") else None,
        project=str(filters["project"]) if filters.get("project") else None,
        topic=str(filters["topic"]) if filters.get("topic") else None,
    )


def _review_range(
    period: str,
    *,
    start: datetime | None,
    end: datetime | None,
    now: datetime | None = None,
) -> tuple[datetime | None, datetime | None]:
    now = now or datetime.now(UTC)
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0), None
    if period == "week":
        return now - timedelta(days=7), None
    if period == "month":
        return now - timedelta(days=30), None
    if period == "custom":
        if not start:
            raise ValueError("Custom review requires start")
        if end and end < start:
            raise ValueError("Review end must not precede start")
        return start, end
    raise ValueError("Unsupported review period")


def review(
    db: Session,
    *,
    period: str = "week",
    start: datetime | None = None,
    end: datetime | None = None,
    source_scope: str = "all",
) -> ReviewOut:
    start, end = _review_range(period, start=start, end=end)
    entries = _visible_entries(db, source_scope=source_scope, start=start, end=end)
    entry_ids = {entry.id for entry in entries}
    counts = {
        "entries": len(entries),
        "problems": sum(_matches_entry(entry, "problems") for entry in entries),
        "solutions": sum(_matches_entry(entry, "solutions") for entry in entries),
        "todo": sum(_matches_entry(entry, "todo") for entry in entries),
        "decisions": sum(_matches_entry(entry, "decisions") for entry in entries),
        "tests_performance": sum(_matches_entry(entry, "tests-performance") for entry in entries),
    }
    memory_statement = (
        select(Memory)
        .where(Memory.status.in_(("active", "conflicted")))
        .order_by(desc(Memory.created_at))
        .limit(MAX_VISIBLE_ENTRIES)
    )
    memories = db.scalars(memory_statement).all()
    if source_scope != "all" and memories:
        memory_ids = {memory.id for memory in memories}
        linked_memory_ids = set(
            db.scalars(
                select(MemorySource.memory_id).where(
                    MemorySource.memory_id.in_(memory_ids),
                    MemorySource.entry_id.in_(entry_ids),
                )
            ).all()
        )
        memories = [
            memory
            for memory in memories
            if memory.source_entry_id is None
            or memory.source_entry_id in entry_ids
            or memory.id in linked_memory_ids
        ]
    ranged_memories = [
        memory
        for memory in memories
        if (not start or (memory.created_at and memory.created_at >= start))
        and (not end or (memory.created_at and memory.created_at <= end))
    ]
    counts["memory_changes"] = len(ranged_memories)
    counts["new_memory"] = sum(memory.status == "active" for memory in ranged_memories)
    counts["conflicted_memory"] = sum(memory.status == "conflicted" for memory in ranged_memories)
    failed_jobs = _failed_job_items(db, limit=MAX_WORKBENCH_ITEMS)
    failed_jobs = [
        item
        for item in failed_jobs
        if item.entry_id in entry_ids
        and (not start or (item.created_at and item.created_at >= start))
        and (not end or (item.created_at and item.created_at <= end))
    ]
    counts["failed_ai_jobs"] = len(failed_jobs)

    items: list[WorkbenchItemOut] = []
    seen_entries: set[UUID] = set()
    for view_id in ("problems", "solutions", "todo", "decisions"):
        for entry in entries:
            if entry.id in seen_entries or not _matches_entry(entry, view_id):
                continue
            seen_entries.add(entry.id)
            items.append(_entry_item(entry, kind=view_id))
            if len(items) >= MAX_WORKBENCH_ITEMS - len(failed_jobs) - len(ranged_memories):
                break
        if len(items) >= MAX_WORKBENCH_ITEMS - len(failed_jobs) - len(ranged_memories):
            break
    items.extend(_memory_item(memory, kind="memory") for memory in ranged_memories[:20])
    items.extend(failed_jobs[:20])
    return ReviewOut(start=start, end=end, counts=counts, items=items[:MAX_WORKBENCH_ITEMS])


def _scope_entries(
    db: Session,
    payload: KnowledgeSummaryInput,
) -> tuple[list[Entry], str]:
    source_scope = validate_source_scope(payload.source_scope)
    scope_type = payload.scope_type.casefold()
    if scope_type not in {"project", "topic", "time"}:
        raise ValueError("Knowledge scope_type must be project, topic or time")
    if scope_type in {"project", "topic"}:
        if not payload.scope_value or not payload.scope_value.strip():
            raise ValueError("Project or topic summary requires scope_value")
        entries = _entries_for_named_observation(
            db,
            observation_type=scope_type,
            name=payload.scope_value.strip(),
            source_scope=source_scope,
        )
        return entries, payload.scope_value.strip()
    return (
        _visible_entries(
            db,
            source_scope=source_scope,
            start=payload.start,
            end=payload.end,
        ),
        payload.scope_value.strip() if payload.scope_value else "时间范围",
    )


def _observation_detail(observation: Observation) -> str:
    data = observation.data_json or {}
    preferred = data.get("summary") or data.get("name") or data.get("reason")
    if isinstance(preferred, str) and preferred.strip():
        return preferred.strip().replace("\n", " ")[:300]
    return json.dumps(data, ensure_ascii=False, sort_keys=True)[:300]


def generate_knowledge_summary(db: Session, payload: KnowledgeSummaryInput) -> Knowledge:
    entries, scope_name = _scope_entries(db, payload)
    entries = sorted(entries, key=lambda entry: (entry.created_at, str(entry.id)))[:MAX_SOURCE_IDS]
    entry_ids = {entry.id for entry in entries}
    memory_ids = _memory_ids_for_entries(db, entry_ids)[:MAX_SOURCE_IDS]
    observations = (
        db.scalars(
            select(Observation)
            .where(Observation.entry_id.in_(entry_ids))
            .order_by(desc(Observation.created_at))
            .limit(120)
        ).all()
        if entry_ids
        else []
    )
    title = f"{payload.scope_type.title()} · {scope_name}"
    lines = [
        f"# {title}",
        "",
        "- 状态：derived",
        f"- 来源 Entry：{len(entry_ids)} 条",
        f"- Active Memory：{len(memory_ids)} 条",
    ]
    if payload.start:
        lines.append(f"- 开始：{payload.start.isoformat()}")
    if payload.end:
        lines.append(f"- 结束：{payload.end.isoformat()}")
    if observations:
        lines.extend(["", "## 关键观察"])
        for observation in observations:
            lines.append(
                f"- `{observation.entry_id}` · {observation.observation_type}："
                f"{redact_secrets(_observation_detail(observation))}"
            )
    if memory_ids:
        memory_rows = db.scalars(select(Memory).where(Memory.id.in_(memory_ids))).all()
        lines.extend(["", "## Active Memory"])
        for memory in sorted(memory_rows, key=lambda item: str(item.id)):
            lines.append(f"- `{memory.id}`：{redact_secrets(memory.memory_text[:500])}")
    lines.extend(["", "## 来源 Entry"])
    for entry in entries:
        lines.append(f"- `{entry.id}` · {_entry_title(entry)} · {entry.created_at.isoformat()}")
    metadata = {
        "scope_type": payload.scope_type.casefold(),
        "scope_value": payload.scope_value,
        "source_scope": payload.source_scope,
        "start": payload.start.isoformat() if payload.start else None,
        "end": payload.end.isoformat() if payload.end else None,
        "entry_ids": [str(entry_id) for entry_id in sorted(entry_ids, key=str)],
        "memory_ids": [str(memory_id) for memory_id in memory_ids],
        "generated_at": datetime.now(UTC).isoformat(),
    }
    knowledge_rows = db.scalars(
        select(Knowledge).where(Knowledge.status == "derived").order_by(desc(Knowledge.updated_at))
    ).all()
    knowledge = next(
        (
            item
            for item in knowledge_rows
            if (item.metadata_json or {}).get("scope_type") == metadata["scope_type"]
            and (item.metadata_json or {}).get("scope_value") == metadata["scope_value"]
            and (item.metadata_json or {}).get("source_scope", "all") == metadata["source_scope"]
            and (item.metadata_json or {}).get("start") == metadata["start"]
            and (item.metadata_json or {}).get("end") == metadata["end"]
        ),
        None,
    )
    if not knowledge:
        knowledge = Knowledge(title=title, content="\n".join(lines), status="derived")
        db.add(knowledge)
    else:
        knowledge.title = title
        knowledge.content = "\n".join(lines)
        knowledge.status = "derived"
    knowledge.metadata_json = metadata
    db.commit()
    db.refresh(knowledge)
    return knowledge


def list_knowledge(db: Session, *, limit: int = 100) -> list[Knowledge]:
    return db.scalars(
        select(Knowledge)
        .where(Knowledge.status == "derived")
        .order_by(desc(Knowledge.updated_at))
        .limit(min(limit, MAX_WORKBENCH_ITEMS))
    ).all()


def similar_entries(
    db: Session,
    entry_id: UUID,
    *,
    source_scope: str = "all",
    limit: int = 5,
) -> list[SimilarEntryOut]:
    validate_source_scope(source_scope)
    entry = db.get(Entry, entry_id)
    if not entry or entry.deleted_at is not None:
        raise ValueError("Entry not found")
    query_text = entry.raw_content[:12_000]
    statement = (
        select(Entry, func.similarity(Entry.raw_content, query_text).label("score"))
        .join(Source, Source.id == Entry.source_id)
        .where(Entry.id != entry.id, Entry.deleted_at.is_(None))
    )
    if source_scope == "native":
        statement = statement.where(Source.is_native.is_(True))
    elif source_scope == "external":
        statement = statement.where(Source.is_native.is_(False))
    statement = statement.order_by(desc("score")).limit(min(max(limit * 4, 20), 100))
    try:
        rows = db.execute(statement).all()
        return [
            SimilarEntryOut(
                entry_id=candidate.id,
                title=candidate.title,
                score=round(max(0.0, min(1.0, float(score or 0.0))), 5),
                reason="PostgreSQL trigram similarity",
                snippet=candidate.raw_content.replace("\n", " ")[:260],
                created_at=candidate.created_at,
            )
            for candidate, score in rows
            if float(score or 0.0) >= 0.08
        ][:limit]
    except SQLAlchemyError:
        db.rollback()
        candidates = _visible_entries(db, source_scope=source_scope)[:500]
        scored = [
            (
                candidate,
                SequenceMatcher(
                    None,
                    query_text.casefold()[:4_000],
                    candidate.raw_content.casefold()[:4_000],
                ).ratio(),
            )
            for candidate in candidates
            if candidate.id != entry.id
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return [
            SimilarEntryOut(
                entry_id=candidate.id,
                title=candidate.title,
                score=round(score, 5),
                reason="Local sequence similarity fallback",
                snippet=candidate.raw_content.replace("\n", " ")[:260],
                created_at=candidate.created_at,
            )
            for candidate, score in scored
            if score >= 0.35
        ][:limit]
