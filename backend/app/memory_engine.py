"""Deterministic salience, reconciliation and transactional Memory Apply."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import AiDerivationMeta, ContentUnit, Memory, MemoryCandidate, MemorySource

Operation = Literal["ADD", "SUPPORT", "SUPERSEDE", "CONFLICT", "MERGE", "IGNORE"]
TEMPORARY_RE = re.compile(r"临时|刚才|暂时|测试|temporary|temporarily|just now", re.I)
UPDATE_RE = re.compile(
    r"最终|后来|改成|变成|更新为|固定为|最终固定|finally|changed to|updated to|set to",
    re.I,
)


@dataclass(frozen=True)
class ReconcileDecision:
    operation: Operation
    target_memory_id: UUID | None = None
    reason: str = ""


def _now() -> datetime:
    return datetime.now(UTC)


def normalize_key(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def scope_key(subject_type: str, subject: str, predicate: str) -> str:
    return f"{subject_type}:{normalize_key(subject)}:{normalize_key(predicate)}"


def evaluate_salience(memory_text: str, requested: str | None = None) -> tuple[str, bool]:
    if TEMPORARY_RE.search(memory_text):
        return "episodic", False
    if requested in {"episodic", "ignore"}:
        return requested, requested == "episodic"
    return "durable", True


def create_candidate(
    db: Session,
    *,
    entry_id: UUID,
    subject: str,
    predicate: str,
    value: str,
    memory_text: str,
    confidence: float = 0.0,
    salience: str | None = None,
    durable: bool | None = None,
    generation: int = 0,
    observation_id: UUID | None = None,
    source_chunk_id: UUID | None = None,
) -> MemoryCandidate:
    if salience is not None and salience not in {"durable", "episodic", "ignore"}:
        raise ValueError("Unsupported memory salience")
    resolved_salience, resolved_durable = evaluate_salience(memory_text, salience)
    candidate = MemoryCandidate(
        entry_id=entry_id,
        observation_id=observation_id,
        source_chunk_id=source_chunk_id,
        subject_type="entity",
        subject_key=normalize_key(subject),
        predicate=normalize_key(predicate),
        scope_key=scope_key("entity", subject, predicate),
        value_json={"value": value},
        value_key=normalize_key(value),
        memory_text=memory_text,
        salience=resolved_salience,
        durable=resolved_durable if durable is None else durable and resolved_salience == "durable",
        confidence=max(0.0, min(1.0, confidence)),
        generation=generation,
    )
    db.add(candidate)
    db.flush()
    return candidate


def retrieve_existing(db: Session, candidate: MemoryCandidate) -> list[Memory]:
    return db.scalars(
        select(Memory)
        .where(
            Memory.scope_key == candidate.scope_key,
            Memory.status.in_(["active", "conflicted", "superseded"]),
        )
        .order_by(Memory.created_at.desc())
    ).all()


def reconcile(candidate: MemoryCandidate, existing: list[Memory]) -> ReconcileDecision:
    if candidate.salience == "ignore":
        return ReconcileDecision("IGNORE", reason="candidate marked ignore")
    active = next((memory for memory in existing if memory.status == "active"), None)
    if not active:
        return ReconcileDecision("ADD", reason="no active memory in scope")
    if active.value_key == candidate.value_key:
        return ReconcileDecision(
            "SUPPORT", target_memory_id=active.id, reason="same normalized value"
        )
    if candidate.salience == "episodic":
        return ReconcileDecision(
            "IGNORE", target_memory_id=active.id, reason="episodic does not replace durable"
        )
    if UPDATE_RE.search(candidate.memory_text):
        return ReconcileDecision(
            "SUPERSEDE", target_memory_id=active.id, reason="explicit update wording"
        )
    return ReconcileDecision(
        "CONFLICT", target_memory_id=active.id, reason="different value without update"
    )


def _lock_scope(db: Session, scope: str) -> None:
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"), {"scope": scope})


def _content_unit_id(db: Session, entry_id: UUID) -> UUID | None:
    unit = db.scalar(
        select(ContentUnit).where(
            ContentUnit.entry_id == entry_id, ContentUnit.owner_type == "entry"
        )
    )
    return unit.id if unit else None


def _add_source(db: Session, memory: Memory, candidate: MemoryCandidate) -> None:
    content_unit_id = _content_unit_id(db, candidate.entry_id)
    exists = db.scalar(
        select(MemorySource).where(
            MemorySource.memory_id == memory.id,
            MemorySource.entry_id == candidate.entry_id,
            MemorySource.content_unit_id == content_unit_id,
        )
    )
    if not exists:
        db.add(
            MemorySource(
                memory_id=memory.id,
                entry_id=candidate.entry_id,
                content_unit_id=content_unit_id,
                support_type="primary",
                confidence=candidate.confidence,
            )
        )


def _new_memory(db: Session, candidate: MemoryCandidate, status: str = "active") -> Memory:
    value = str(candidate.value_json.get("value", candidate.value_key))
    memory = Memory(
        subject_type=candidate.subject_type,
        subject_key=candidate.subject_key,
        predicate=candidate.predicate,
        scope_key=candidate.scope_key,
        value_json=candidate.value_json,
        value_key=candidate.value_key,
        memory_text=candidate.memory_text,
        status=status,
        salience=candidate.salience,
        durable=candidate.durable,
        confidence=candidate.confidence,
        recorded_at=_now(),
        observed_at=_now(),
        source_entry_id=candidate.entry_id,
        source_chunk_id=candidate.source_chunk_id,
        metadata_json={"value_text": value},
    )
    db.add(memory)
    db.flush()
    _add_source(db, memory, candidate)
    if candidate.observation_id:
        provenance = db.scalar(
            select(AiDerivationMeta).where(
                AiDerivationMeta.object_type == "observation",
                AiDerivationMeta.object_id == candidate.observation_id,
            )
        )
        if provenance:
            db.add(
                AiDerivationMeta(
                    object_type="memory",
                    object_id=memory.id,
                    provider=provenance.provider,
                    model=provenance.model,
                    prompt_name=provenance.prompt_name,
                    prompt_version=provenance.prompt_version,
                    schema_version=provenance.schema_version,
                    prompt_hash=provenance.prompt_hash,
                )
            )
    return memory


def apply_candidate(
    db: Session, candidate: MemoryCandidate
) -> tuple[ReconcileDecision, Memory | None]:
    """Apply a validated candidate under a PostgreSQL transaction advisory lock."""
    _lock_scope(db, candidate.scope_key)
    existing = retrieve_existing(db, candidate)
    decision = reconcile(candidate, existing)
    memory: Memory | None = None
    if decision.operation == "ADD":
        memory = _new_memory(db, candidate)
    elif decision.operation in {"SUPPORT", "MERGE"}:
        memory = db.get(Memory, decision.target_memory_id) if decision.target_memory_id else None
        if not memory:
            raise ValueError("Reconcile target memory does not exist")
        _add_source(db, memory, candidate)
    elif decision.operation == "SUPERSEDE":
        old = db.get(Memory, decision.target_memory_id) if decision.target_memory_id else None
        if not old or old.status != "active":
            raise ValueError("Supersede target memory is not active")
        old.status = "superseded"
        old.superseded_at = _now()
        db.flush()
        memory = _new_memory(db, candidate)
        old.superseded_by = memory.id
    elif decision.operation == "CONFLICT":
        old = db.get(Memory, decision.target_memory_id) if decision.target_memory_id else None
        if old and old.status == "active":
            old.status = "conflicted"
        memory = _new_memory(db, candidate, status="conflicted")
    candidate.status = "ignored" if decision.operation == "IGNORE" else "applied"
    db.commit()
    return decision, memory


def confirm_memory(db: Session, memory_id: UUID) -> Memory:
    memory = db.get(Memory, memory_id)
    if not memory:
        raise ValueError("Memory not found")
    _lock_scope(db, memory.scope_key)
    selected = db.get(Memory, memory_id)
    if not selected or selected.status == "deleted":
        raise ValueError("Memory cannot be confirmed")
    others = db.scalars(
        select(Memory).where(
            Memory.scope_key == selected.scope_key,
            Memory.id != selected.id,
            Memory.status == "active",
        )
    ).all()
    for other in others:
        other.status = "conflicted"
    selected.status = "active"
    db.commit()
    db.refresh(selected)
    return selected


def expire_memory(db: Session, memory: Memory) -> Memory:
    if memory.status == "deleted":
        raise ValueError("Memory cannot be expired")
    memory.status = "expired"
    memory.expired_at = memory.expired_at or _now()
    memory.valid_to = memory.valid_to or memory.expired_at
    db.commit()
    db.refresh(memory)
    return memory


def delete_memory(db: Session, memory: Memory) -> None:
    memory.status = "deleted"
    db.commit()
