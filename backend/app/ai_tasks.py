"""Independent, idempotent enrichment jobs for one Entry generation."""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.memory_engine import create_candidate
from app.models import (
    AiDerivationMeta,
    AIJob,
    ContentUnit,
    Entity,
    Entry,
    EntryEntity,
    EntryTag,
    Observation,
    Project,
    Relation,
    Tag,
    Topic,
)
from app.prompting import PromptValidationError, resolve_prompt, validate_output
from app.providers import (
    ChatProvider,
    ProviderNotConfigured,
    ProviderRequestError,
    ProviderUnavailable,
    get_chat_provider,
    task_messages,
)
from app.routing import task_route
from app.secret_scanner import redact_secrets

_UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f-]{27}\b", re.I)
_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_WWN_RE = re.compile(r"\b(?:naa\.)?[0-9a-f]{16,}\b", re.I)
_HOST_RE = re.compile(r"\b(?:node|host|srv|vm)[-_][a-z0-9.-]+\b", re.I)
_DOMAIN_RE = re.compile(r"\b[a-z0-9-]+(?:\.[a-z0-9-]+)+\b", re.I)
_TEMPORARY_RE = re.compile(r"临时|刚才|暂时|测试|temporary|temporarily|just now", re.I)
_TIME_HINT_RE = re.compile(r"以前|过去|现在|后来|最终|去年|上个月|最近|临时|曾经|昨天|今天")


def _now() -> datetime:
    return datetime.now(UTC)


def _normalise(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _prompt_for(db: Session, entry: Entry, name: str):
    return resolve_prompt(
        db,
        name,
        {"entry_id": str(entry.id), "content": entry.raw_content[:12_000]},
    )


def _record_meta(
    db: Session,
    *,
    object_type: str,
    object_id,
    provider: str,
    model: str,
    prompt_name: str,
    prompt_version: int,
    schema_version: str | None,
    prompt_hash: str,
) -> None:
    existing = db.scalar(
        select(AiDerivationMeta).where(
            AiDerivationMeta.object_type == object_type,
            AiDerivationMeta.object_id == object_id,
        )
    )
    if existing:
        existing.provider = provider
        existing.model = model
        existing.prompt_name = prompt_name
        existing.prompt_version = prompt_version
        existing.schema_version = schema_version
        existing.prompt_hash = prompt_hash
        existing.generated_at = _now()
    else:
        db.add(
            AiDerivationMeta(
                object_type=object_type,
                object_id=object_id,
                provider=provider,
                model=model,
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                schema_version=schema_version,
                prompt_hash=prompt_hash,
            )
        )


def _record_observation(
    db: Session,
    entry: Entry,
    *,
    observation_type: str,
    data: dict[str, Any],
    generation: int,
    provider: str,
    model: str,
    prompt_name: str,
    prompt_version: int,
    schema_version: str | None,
    prompt_hash: str,
) -> Observation | None:
    locked = db.scalar(
        select(Observation).where(
            Observation.entry_id == entry.id,
            Observation.observation_type == observation_type,
            Observation.is_user_locked.is_(True),
        )
    )
    if locked:
        # A user decision wins over any later AI regeneration.
        return None
    observation = db.scalar(
        select(Observation).where(
            Observation.entry_id == entry.id,
            Observation.observation_type == observation_type,
            Observation.generation == generation,
        )
    )
    if not observation:
        content_unit = db.scalar(
            select(ContentUnit).where(
                ContentUnit.entry_id == entry.id, ContentUnit.owner_type == "entry"
            )
        )
        observation = Observation(
            entry_id=entry.id,
            content_unit_id=content_unit.id if content_unit else None,
            observation_type=observation_type,
            data_json=data,
            source="ai" if provider != "deterministic" else "rule",
            generation=generation,
        )
        db.add(observation)
        db.flush()
    else:
        observation.data_json = data
    _record_meta(
        db,
        object_type="observation",
        object_id=observation.id,
        provider=provider,
        model=model,
        prompt_name=prompt_name,
        prompt_version=prompt_version,
        schema_version=schema_version,
        prompt_hash=prompt_hash,
    )
    return observation


def _deterministic_prompt_meta(db: Session, entry: Entry, prompt_name: str):
    resolved = _prompt_for(db, entry, prompt_name)
    return "deterministic", "rules", resolved


def _classify(entry: Entry) -> dict[str, Any]:
    """Multi-class rule classification: order encodes priority for the primary type."""
    content = entry.raw_content.lower()
    types: list[str] = []
    if any(term in content for term in ("error", "exception", "故障", "问题", "失败")):
        types.append("troubleshooting")
    if "todo" in content or "待办" in content:
        types.append("todo")
    if any(term in content for term in ("决定", "最终", "固定", "decision")):
        types.append("decision")
    if any(term in content for term in ("参考", "reference", "链接")):
        types.append("reference")
    if any(term in content for term in ("测试", "test")):
        types.append("test")
    if any(term in content for term in ("性能", "performance", "benchmark")):
        types.append("performance")
    if "```" in content or "#!/" in content:
        types.append("code")
    if not types:
        types.append(entry.content_type or "note")
    primary = types[0]
    return {
        "content_type": primary,
        "content_types": list(dict.fromkeys(types)),
        "confidence": 0.7,
        "reason": "rule-based classification",
    }


def _deterministic_entities(content: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    patterns = (
        ("uuid", _UUID_RE),
        ("ip", _IP_RE),
        ("wwn", _WWN_RE),
        ("host", _HOST_RE),
        ("domain", _DOMAIN_RE),
    )
    for entity_type, pattern in patterns:
        for match in pattern.findall(content):
            normalized = _normalise(match)
            key = entity_type, normalized
            if key not in seen:
                seen.add(key)
                found.append(
                    {
                        "name": match,
                        "entity_type": entity_type,
                        "mention_text": match,
                        "confidence": 0.99,
                    }
                )
    return found[:32]


def _persist_entities(db: Session, entry: Entry, values: list[dict[str, Any]]) -> None:
    for value in values:
        normalized = _normalise(value["name"])
        entity = db.scalar(
            select(Entity).where(
                Entity.entity_type == value["entity_type"], Entity.normalized_name == normalized
            )
        )
        if not entity:
            entity = Entity(
                entity_type=value["entity_type"],
                canonical_name=value["name"],
                normalized_name=normalized,
            )
            db.add(entity)
            db.flush()
        link = db.get(EntryEntity, (entry.id, entity.id))
        if not link:
            db.add(
                EntryEntity(
                    entry_id=entry.id,
                    entity_id=entity.id,
                    mention_text=value["mention_text"],
                    confidence=value.get("confidence"),
                    source="ai",
                )
            )
        elif link.source == "user":
            # User-confirmed entities are not overwritten by later AI runs.
            continue


def _deterministic_tags(content: str) -> list[str]:
    terms = (
        "iscsi",
        "multipath",
        "openstack",
        "storage",
        "gpu",
        "docker",
        "postgresql",
        "redis",
    )
    lower = content.casefold()
    return [term for term in terms if term in lower]


def _persist_tags(db: Session, entry: Entry, names: list[str]) -> None:
    for name in dict.fromkeys(_normalise(value) for value in names if value.strip()):
        tag = db.scalar(select(Tag).where(Tag.normalized_name == name))
        if not tag:
            tag = Tag(name=name, normalized_name=name, source="ai")
            db.add(tag)
            db.flush()
        link = db.get(EntryTag, (entry.id, tag.id))
        if not link:
            db.add(EntryTag(entry_id=entry.id, tag_id=tag.id, source="ai"))
        elif link.user_removed or link.user_confirmed:
            continue


def _run_deterministic(
    db: Session, entry: Entry, job: AIJob, prompt_name: str
) -> tuple[Any, str, str, Any]:
    provider, model, resolved = _deterministic_prompt_meta(db, entry, prompt_name)
    if prompt_name == "classification":
        value = _classify(entry)
    elif prompt_name == "entity_extract":
        value = {"entities": _deterministic_entities(entry.raw_content)}
    elif prompt_name == "time_extract":
        value = {
            "expressions": _TIME_HINT_RE.findall(entry.raw_content)[:16],
            "confidence": 0.9,
        }
    elif prompt_name == "tag":
        value = {"tags": _deterministic_tags(entry.raw_content)}
    else:
        raise ProviderUnavailable(f"No deterministic handler for {prompt_name}")
    return validate_output(prompt_name, value), provider, model, resolved


def _run_chat(
    db: Session, entry: Entry, prompt_name: str, provider: ChatProvider | None
) -> tuple[Any, str, str, Any, int | None]:
    resolved = _prompt_for(db, entry, prompt_name)
    provider_name, model = task_route(db, prompt_name, resolved)
    provider = provider or get_chat_provider(
        model_override=model,
        provider_override=provider_name,
    )
    result = provider.complete(
        task_messages(redact_secrets(resolved.content)),
        max_tokens=800,
        temperature=0.0,
        json_mode=True,
    )
    return (
        validate_output(prompt_name, result.content),
        provider.name,
        result.model,
        resolved,
        result.token_usage,
    )


def _persist_output(
    db: Session,
    entry: Entry,
    job: AIJob,
    prompt_name: str,
    output: Any,
    provider: str,
    model: str,
    resolved,
) -> None:
    data = output.model_dump()
    meta = {
        "provider": provider,
        "model": model,
        "prompt_name": prompt_name,
        "prompt_version": resolved.version,
        "schema_version": resolved.schema_version,
        "prompt_hash": resolved.prompt_hash,
    }
    if prompt_name == "classification":
        locked = db.scalar(
            select(Observation).where(
                Observation.entry_id == entry.id,
                Observation.observation_type == "classification",
                Observation.is_user_locked.is_(True),
            )
        )
        if not locked:
            types = [
                str(value).strip()
                for value in (data.get("content_types") or [])
                if str(value).strip()
            ]
            primary = str(data.get("content_type") or entry.content_type or "note").strip()
            if primary and primary not in types:
                types.insert(0, primary)
            if types:
                entry.content_type = primary
                entry.content_types = list(dict.fromkeys(types))[:16]
        _record_observation(
            db,
            entry,
            observation_type="classification",
            data=data,
            generation=job.generation,
            **meta,
        )
    elif prompt_name == "summary":
        _record_observation(
            db, entry, observation_type="summary", data=data, generation=job.generation, **meta
        )
    elif prompt_name == "observation_extract":
        _record_observation(
            db, entry, observation_type="observation", data=data, generation=job.generation, **meta
        )
    elif prompt_name == "entity_extract":
        _persist_entities(db, entry, data["entities"])
        _record_observation(
            db, entry, observation_type="entities", data=data, generation=job.generation, **meta
        )
    elif prompt_name == "tag":
        _persist_tags(db, entry, data["tags"])
        _record_observation(
            db, entry, observation_type="tags", data=data, generation=job.generation, **meta
        )
    elif prompt_name == "time_extract":
        _record_observation(
            db, entry, observation_type="temporal", data=data, generation=job.generation, **meta
        )
    elif prompt_name == "project_classify":
        if (
            _record_observation(
                db, entry, observation_type="project", data=data, generation=job.generation, **meta
            )
            is None
        ):
            return
        project = db.scalar(select(Project).where(Project.name == data["name"]))
        if not project:
            db.add(Project(name=data["name"], source="ai"))
    elif prompt_name == "topic_classify":
        if (
            _record_observation(
                db, entry, observation_type="topic", data=data, generation=job.generation, **meta
            )
            is None
        ):
            return
        topic = db.scalar(select(Topic).where(Topic.name == data["name"]))
        if not topic:
            db.add(Topic(name=data["name"], source="ai"))
    elif prompt_name == "relation_build":
        _record_observation(
            db, entry, observation_type="relations", data=data, generation=job.generation, **meta
        )
        for relation in data["relations"]:
            try:
                relation_type = str(relation["relation_type"])
                target_type = str(relation["target_type"])
                target_id = UUID(str(relation["target_id"]))
                exists = db.scalar(
                    select(Relation).where(
                        Relation.source_type == "entry",
                        Relation.source_id == entry.id,
                        Relation.relation_type == relation_type,
                        Relation.target_type == target_type,
                        Relation.target_id == target_id,
                    )
                )
                if not exists:
                    db.add(
                        Relation(
                            source_type="entry",
                            source_id=entry.id,
                            relation_type=relation_type,
                            target_type=target_type,
                            target_id=target_id,
                            confidence=relation.get("confidence"),
                        )
                    )
            except (KeyError, TypeError, ValueError):
                continue
    elif prompt_name == "memory_extract":
        observation = _record_observation(
            db,
            entry,
            observation_type="memory_candidates",
            data=data,
            generation=job.generation,
            **meta,
        )
        if observation is None:
            return
        for candidate in data["candidates"]:
            create_candidate(
                db,
                entry_id=entry.id,
                subject=candidate["subject"],
                predicate=candidate["predicate"],
                value=candidate["value"],
                memory_text=candidate["memory_text"],
                confidence=candidate["confidence"],
                salience=candidate["salience"],
                durable=candidate["durable"],
                generation=job.generation,
                observation_id=observation.id,
            )


def run_ai_job(
    db: Session,
    entry: Entry,
    job: AIJob,
    *,
    chat_provider: ChatProvider | None = None,
) -> bool:
    if job.status == "done":
        return True
    prompt_name = {
        "classify": "classification",
        "summarize": "summary",
        "tag": "tag",
        "entity_extract": "entity_extract",
        "time_extract": "time_extract",
        "project_classify": "project_classify",
        "topic_classify": "topic_classify",
        "memory_extract": "memory_extract",
        "relation_build": "relation_build",
    }.get(job.job_type)
    if not prompt_name:
        return False
    job.status = "running"
    job.attempt += 1
    job.started_at = _now()
    job.error = None
    db.commit()
    started = time.perf_counter()
    try:
        if prompt_name in {"classification", "entity_extract", "time_extract", "tag"}:
            output, provider, model, resolved = _run_deterministic(db, entry, job, prompt_name)
            token_usage = None
        else:
            output, provider, model, resolved, token_usage = _run_chat(
                db, entry, prompt_name, chat_provider
            )
        job.provider = provider
        job.model = model
        job.token_usage = token_usage
        _persist_output(db, entry, job, prompt_name, output, provider, model, resolved)
        job.status = "done"
        job.finished_at = _now()
        job.latency_ms = round((time.perf_counter() - started) * 1000)
        db.commit()
        return True
    except PromptValidationError:
        db.rollback()
        job = db.get(AIJob, job.id)
        job.status = "prompt_validation_failed"
        job.error = "Prompt Validation Failed"
    except ProviderNotConfigured:
        db.rollback()
        job = db.get(AIJob, job.id)
        job.status = "skipped"
        job.error = "provider_not_configured"
    except (ProviderUnavailable, ProviderRequestError) as exc:
        db.rollback()
        job = db.get(AIJob, job.id)
        job.status = "failed"
        job.error = str(exc)[:500]
    except Exception as exc:
        db.rollback()
        job = db.get(AIJob, job.id)
        job.status = "failed"
        job.error = type(exc).__name__
    job.finished_at = _now()
    job.latency_ms = round((time.perf_counter() - started) * 1000)
    db.commit()
    return False
