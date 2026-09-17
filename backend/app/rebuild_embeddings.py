"""Rebuild retrieval chunks and embeddings from persisted Raw Entries."""

from __future__ import annotations

import argparse
import logging
import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Entry
from app.providers import ProviderUnavailable, get_embedding_provider
from app.services.embeddings import embed_chunks, embed_memories, rebuild_chunks

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry-id", help="Only rebuild one Entry")
    args = parser.parse_args()
    with SessionLocal() as db:
        statement = select(Entry).where(Entry.deleted_at.is_(None)).order_by(Entry.created_at)
        if args.entry_id:
            statement = statement.where(Entry.id == args.entry_id)
        entries = db.scalars(statement).all()
        try:
            for entry in entries:
                rebuild_chunks(db, entry)
            db.commit()
            provider = get_embedding_provider()
            total = embed_chunks(db, entry_id=args.entry_id, provider=provider)
            memories = embed_memories(db, provider=provider)
        except ProviderUnavailable as exc:
            db.rollback()
            logger.error("embedding rebuild unavailable: %s", str(exc))
            return 2
    print(f"rebuilt {total} chunk embeddings and {memories} memory embeddings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
