from __future__ import annotations

from uuid import uuid4

from sqlalchemy import delete, select

from app.db import SessionLocal
from app.knowledge import create_knowledge
from app.memory_engine import apply_candidate, create_candidate
from app.models import ContentUnit, Entry, Knowledge, Memory, Source


def test_knowledge_hook_keeps_atomic_memory_as_source():
    entry_id = None
    knowledge_id = None
    memory_id = None
    with SessionLocal() as db:
        source = db.scalar(select(Source).where(Source.is_native.is_(True)))
        entry = Entry(source_id=source.id, raw_content=f"knowledge fixture {uuid4()}")
        db.add(entry)
        db.flush()
        entry_id = entry.id
        db.add(
            ContentUnit(
                owner_type="entry",
                owner_id=entry.id,
                source_id=source.id,
                entry_id=entry.id,
                content=entry.raw_content,
            )
        )
        db.commit()
        candidate = create_candidate(
            db,
            entry_id=entry.id,
            subject="fixture",
            predicate="status",
            value="active",
            memory_text="fixture status is active",
        )
        _, memory = apply_candidate(db, candidate)
        memory_id = memory.id
        knowledge = create_knowledge(
            db,
            title="Fixture knowledge",
            content="Derived context",
            memory_ids=[memory.id],
        )
        knowledge_id = knowledge.id
        assert str(memory.id) in knowledge.metadata_json["memory_ids"]
        assert db.get(Memory, memory.id).status == "active"

    with SessionLocal() as db:
        db.execute(delete(Knowledge).where(Knowledge.id == knowledge_id))
        db.execute(delete(Memory).where(Memory.id == memory_id))
        db.execute(delete(Entry).where(Entry.id == entry_id))
        db.commit()
