from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from sqlalchemy import delete, select

from app.db import SessionLocal
from app.memory_engine import apply_candidate, create_candidate, evaluate_salience
from app.models import ContentUnit, Entry, Memory, MemoryCandidate, MemorySource, Source


def _entry_id(raw_content: str):
    with SessionLocal() as db:
        source = db.scalar(select(Source).where(Source.is_native.is_(True)))
        entry = Entry(source_id=source.id, raw_content=raw_content)
        db.add(entry)
        db.flush()
        db.add(
            ContentUnit(
                owner_type="entry",
                owner_id=entry.id,
                source_id=source.id,
                entry_id=entry.id,
                content=raw_content,
            )
        )
        db.commit()
        return entry.id


def test_salience_keeps_temporary_values_out_of_durable_scope():
    assert evaluate_salience("V100 最终固定 150W") == ("durable", True)
    assert evaluate_salience("刚才临时测试 175W") == ("episodic", False)


def test_reconcile_support_supersede_and_conflict_are_deterministic():
    entry_id = _entry_id("memory engine fixture")
    memory_ids = []
    try:
        with SessionLocal() as db:
            first = create_candidate(
                db,
                entry_id=entry_id,
                subject="V100",
                predicate="power_limit",
                value="180W",
                memory_text="V100 设置 180W",
                confidence=0.9,
            )
            decision, memory = apply_candidate(db, first)
            assert decision.operation == "ADD"
            assert memory
            memory_ids.append(memory.id)

            support = create_candidate(
                db,
                entry_id=entry_id,
                subject="V100",
                predicate="power_limit",
                value="180W",
                memory_text="V100 仍然是 180W",
                confidence=0.8,
            )
            decision, supported = apply_candidate(db, support)
            assert decision.operation == "SUPPORT"
            assert supported.id == memory.id
            assert db.scalar(select(MemorySource.id).where(MemorySource.memory_id == memory.id))

            supersede = create_candidate(
                db,
                entry_id=entry_id,
                subject="V100",
                predicate="power_limit",
                value="150W",
                memory_text="后来最终改成 150W",
                confidence=0.95,
            )
            decision, current = apply_candidate(db, supersede)
            assert decision.operation == "SUPERSEDE"
            assert current and current.status == "active"
            memory_ids.append(current.id)
            old = db.get(Memory, memory.id)
            assert old and old.status == "superseded" and old.superseded_by == current.id

            episodic = create_candidate(
                db,
                entry_id=entry_id,
                subject="V100",
                predicate="power_limit",
                value="175W",
                memory_text="刚才临时测试 175W",
                salience="episodic",
                confidence=0.7,
            )
            decision, ignored = apply_candidate(db, episodic)
            assert decision.operation == "IGNORE"
            assert ignored is None

            port = create_candidate(
                db,
                entry_id=entry_id,
                subject="Lumen",
                predicate="default_port",
                value="8080",
                memory_text="Lumen 默认端口是 8080",
            )
            _, port_memory = apply_candidate(db, port)
            memory_ids.append(port_memory.id)
            conflict = create_candidate(
                db,
                entry_id=entry_id,
                subject="Lumen",
                predicate="default_port",
                value="8081",
                memory_text="Lumen 默认端口是 8081",
            )
            decision, conflicted = apply_candidate(db, conflict)
            assert decision.operation == "CONFLICT"
            assert conflicted and conflicted.status == "conflicted"
            assert db.get(Memory, port_memory.id).status == "conflicted"
            memory_ids.append(conflicted.id)
    finally:
        with SessionLocal() as db:
            db.execute(delete(Memory).where(Memory.id.in_(memory_ids)))
            db.execute(delete(Entry).where(Entry.id == entry_id))
            db.commit()


def test_concurrent_same_scope_candidates_keep_one_active_memory():
    subject = f"Concurrent-{uuid4()}"
    entry_ids = [_entry_id("concurrency fixture one"), _entry_id("concurrency fixture two")]
    candidate_ids = []
    try:
        with SessionLocal() as db:
            for entry_id in entry_ids:
                candidate = create_candidate(
                    db,
                    entry_id=entry_id,
                    subject=subject,
                    predicate="port",
                    value="8080",
                    memory_text="default port is 8080",
                    confidence=0.8,
                )
                db.commit()
                candidate_ids.append(candidate.id)

        def apply(candidate_id):
            with SessionLocal() as db:
                decision, memory = apply_candidate(db, db.get(MemoryCandidate, candidate_id))
                return decision.operation, memory.id

        with ThreadPoolExecutor(max_workers=2) as executor:
            decisions = list(executor.map(apply, candidate_ids))
        assert sorted(operation for operation, _ in decisions) == ["ADD", "SUPPORT"]
        with SessionLocal() as db:
            active = db.scalars(
                select(Memory).where(
                    Memory.scope_key == f"entity:{subject.casefold()}:port",
                    Memory.status == "active",
                )
            ).all()
            assert len(active) == 1
            assert db.scalar(select(MemorySource.id).where(MemorySource.memory_id == active[0].id))
    finally:
        with SessionLocal() as db:
            memory_ids = db.scalars(
                select(Memory.id).where(Memory.scope_key == f"entity:{subject.casefold()}:port")
            ).all()
            db.execute(delete(Memory).where(Memory.id.in_(memory_ids)))
            db.execute(delete(Entry).where(Entry.id.in_(entry_ids)))
            db.commit()
