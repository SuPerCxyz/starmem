from __future__ import annotations

from uuid import uuid4

from sqlalchemy import delete, select

from app.db import SessionLocal
from app.models import ContentUnit, Entry, ExternalItem, Source
from app.services.external_ingest import upsert_external_snapshot
from app.services.search import search_fulltext


class FixtureAdapter:
    def __init__(self, content: str):
        self.content = content

    def discover(self, cursor=None):
        yield "fixture-1"

    def fetch_item(self, external_id):
        return {"id": external_id, "body": self.content}

    def normalize(self, raw_item):
        return {
            "external_id": raw_item["id"],
            "title": "Fixture item",
            "raw_content": raw_item["body"],
            "item_type": "document",
            "metadata_json": {"fixture": True},
        }

    def get_cursor(self):
        return "fixture-v1"


def test_external_snapshot_is_idempotent_and_does_not_create_entry():
    source_id = None
    try:
        with SessionLocal() as db:
            source = Source(
                name=f"Fixture {uuid4()}",
                source_type="fixture",
                is_native=False,
            )
            db.add(source)
            db.flush()
            source_id = source.id
            adapter = FixtureAdapter("external read-only content")
            normalized = adapter.normalize(adapter.fetch_item("fixture-1"))
            normalized["metadata_json"] = {"fixture": True, "url": "https://example.test/item/1"}
            first, changed = upsert_external_snapshot(db, source, normalized)
            db.commit()
            assert changed is True
            second, changed = upsert_external_snapshot(db, source, normalized)
            db.commit()
            assert changed is False
            assert first.id == second.id
            assert db.scalar(select(Entry).where(Entry.source_id == source.id)) is None
            unit = db.scalar(select(ContentUnit).where(ContentUnit.external_item_id == first.id))
            assert unit and unit.owner_type == "external_item"
            assert unit.content == "external read-only content"
            results = search_fulltext(db, "external read-only", source_scope="external")
            assert results and results[0].external_id == "fixture-1"
            assert results[0].external_url == "https://example.test/item/1"
    finally:
        if source_id:
            with SessionLocal() as db:
                item_ids = db.scalars(
                    select(ExternalItem.id).where(ExternalItem.source_id == source_id)
                ).all()
                db.execute(delete(ContentUnit).where(ContentUnit.external_item_id.in_(item_ids)))
                db.execute(delete(ExternalItem).where(ExternalItem.source_id == source_id))
                db.execute(delete(Source).where(Source.id == source_id))
                db.commit()
