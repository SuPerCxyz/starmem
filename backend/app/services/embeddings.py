"""Chunk embedding persistence and rebuild helpers."""

from __future__ import annotations

import time
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import ContentUnit, Entry, EntryChunk, Memory
from app.providers import EmbeddingProvider, ProviderUnavailable, get_embedding_provider
from app.services.chunking import chunk_text


def rebuild_chunks(db: Session, entry: Entry) -> list[EntryChunk]:
    content_unit = db.scalar(
        select(ContentUnit).where(
            ContentUnit.entry_id == entry.id, ContentUnit.owner_type == "entry"
        )
    )
    if not content_unit:
        raise ValueError(f"Entry ContentUnit not found: {entry.id}")
    db.execute(delete(EntryChunk).where(EntryChunk.entry_id == entry.id))
    db.flush()
    chunks = chunk_text(entry.raw_content, content_format=entry.content_format)
    rows = [
        EntryChunk(
            entry_id=entry.id,
            content_unit_id=content_unit.id,
            chunk_index=index,
            chunk_type=chunk.chunk_type,
            content=chunk.content,
            token_count=chunk.token_count,
            start_offset=chunk.start_offset,
            end_offset=chunk.end_offset,
            metadata_json=chunk.metadata,
        )
        for index, chunk in enumerate(chunks)
    ]
    db.add_all(rows)
    db.flush()
    return rows


def embed_chunks(
    db: Session,
    *,
    entry_id: UUID | None = None,
    provider: EmbeddingProvider | None = None,
) -> int:
    provider = provider or get_embedding_provider()
    if provider is None:
        raise ProviderUnavailable("Embedding provider is disabled")
    statement = select(EntryChunk).order_by(EntryChunk.entry_id, EntryChunk.chunk_index)
    if entry_id:
        statement = statement.where(EntryChunk.entry_id == entry_id)
    chunks = db.scalars(statement).all()
    if not chunks:
        return 0
    vectors = provider.embed([chunk.content for chunk in chunks])
    for chunk, vector in zip(chunks, vectors, strict=True):
        chunk.embedding = vector
    db.commit()
    return len(chunks)


def embed_memories(
    db: Session, *, provider: EmbeddingProvider | None = None, active_only: bool = True
) -> int:
    provider = provider or get_embedding_provider()
    if provider is None:
        raise ProviderUnavailable("Embedding provider is disabled")
    statement = select(Memory).order_by(Memory.created_at)
    if active_only:
        statement = statement.where(Memory.status == "active")
    memories = db.scalars(statement).all()
    if not memories:
        return 0
    vectors = provider.embed([memory.memory_text for memory in memories])
    for memory, vector in zip(memories, vectors, strict=True):
        memory.embedding = vector
    db.commit()
    return len(memories)


def rebuild_entry_embeddings(db: Session, entry: Entry) -> int:
    rebuild_chunks(db, entry)
    db.commit()
    return embed_chunks(db, entry_id=entry.id)


def timed_embed(provider: EmbeddingProvider, texts: list[str]) -> tuple[list[list[float]], int]:
    started = time.perf_counter()
    vectors = provider.embed(texts)
    return vectors, round((time.perf_counter() - started) * 1000)
