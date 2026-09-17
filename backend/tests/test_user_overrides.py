from __future__ import annotations

from uuid import uuid4

from sqlalchemy import delete, select

from app.ai_tasks import _persist_entities, _persist_tags
from app.db import SessionLocal
from app.models import Entity, Entry, EntryEntity, EntryTag, Source, Tag


def test_user_metadata_overrides_survive_deterministic_reprocessing():
    entry_id = None
    tag_id = None
    entity_id = None
    with SessionLocal() as db:
        source = db.scalar(select(Source).where(Source.is_native.is_(True)))
        entry = Entry(source_id=source.id, raw_content=f"override fixture {uuid4()}")
        db.add(entry)
        db.flush()
        entry_id = entry.id
        tag = Tag(name=f"User Tag {uuid4()}", normalized_name=f"user-tag-{uuid4()}", source="user")
        db.add(tag)
        db.flush()
        tag_id = tag.id
        db.add(EntryTag(entry_id=entry.id, tag_id=tag.id, source="user", user_confirmed=True))
        entity_name = f"user-host-{uuid4()}"
        entity = Entity(entity_type="host", canonical_name=entity_name, normalized_name=entity_name)
        db.add(entity)
        db.flush()
        entity_id = entity.id
        db.add(
            EntryEntity(
                entry_id=entry.id,
                entity_id=entity.id,
                mention_text=entity.canonical_name,
                confidence=1.0,
                source="user",
            )
        )
        db.commit()
        _persist_tags(db, entry, [tag.name])
        _persist_entities(
            db,
            entry,
            [
                {
                    "name": entity.canonical_name,
                    "entity_type": "host",
                    "mention_text": entity.canonical_name,
                    "confidence": 0.2,
                }
            ],
        )
        db.commit()
        link = db.get(EntryTag, (entry.id, tag.id))
        entity_link = db.get(EntryEntity, (entry.id, entity.id))
        assert link and link.source == "user" and link.user_confirmed
        assert entity_link and entity_link.source == "user" and entity_link.confidence == 1.0

    with SessionLocal() as db:
        db.execute(delete(Entry).where(Entry.id == entry_id))
        db.execute(delete(Tag).where(Tag.id == tag_id))
        db.execute(delete(Entity).where(Entity.id == entity_id))
        db.commit()
