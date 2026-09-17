"""Reproducible local benchmarks for StarMem capture and retrieval paths.

Usage (inside the api container, or on a host with the backend deps installed):

    docker compose exec -T api python scripts/benchmark.py --entries 2000 --json /tmp/bench.json

Measured operations: Raw save, PostgreSQL FTS, Hybrid retrieval and Ask local
retrieval. The script never calls remote providers and never deletes user data;
it removes only the fixtures carrying its own run marker.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ask import ask
from app.db import SessionLocal
from app.models import ContentUnit, Entry, EntryVersion, Source
from app.schemas import AskRequest
from app.services.embeddings import embed_chunks, rebuild_chunks
from app.services.search import search


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(percentile * (len(ordered) - 1))))
    return round(ordered[index], 2)


def _native_source_id(db: Session) -> UUID:
    source = db.scalar(select(Source).where(Source.is_native.is_(True)))
    if not source:
        raise RuntimeError("Native source not found; run the seed step first")
    return source.id


def _insert_raw(db: Session, *, source_id: UUID, title: str, body: str) -> Entry:
    """Insert an Entry the same way the Raw-first capture path does, without AI jobs."""
    entry = Entry(source_id=source_id, title=title, raw_content=body, content_type="note")
    db.add(entry)
    db.flush()
    db.add(
        EntryVersion(
            entry_id=entry.id,
            version_number=1,
            raw_content=entry.raw_content,
            title=entry.title,
            change_source="benchmark",
        )
    )
    db.add(
        ContentUnit(
            owner_type="entry",
            owner_id=entry.id,
            source_id=source_id,
            entry_id=entry.id,
            unit_type="entry",
            content=entry.raw_content,
        )
    )
    db.commit()
    return entry


def _measure(label: str, samples: int, operation) -> dict[str, float | int | str]:
    timings: list[float] = []
    for _ in range(samples):
        started = time.perf_counter()
        operation()
        timings.append((time.perf_counter() - started) * 1000)
    return {
        "operation": label,
        "samples": samples,
        "p50_ms": _percentile(timings, 0.50),
        "p95_ms": _percentile(timings, 0.95),
        "mean_ms": round(statistics.fmean(timings), 2),
        "max_ms": round(max(timings), 2),
    }


def _embed_subset(db: Session, *, entry_ids: list[UUID], limit: int) -> int:
    """Chunk and embed a subset so the semantic path has real vectors."""
    embedded = 0
    for entry_id in entry_ids[:limit]:
        entry = db.get(Entry, entry_id)
        if entry is None:
            continue
        rebuild_chunks(db, entry)
        db.commit()
        embedded += embed_chunks(db, entry_id=entry_id)
    return embedded


def _seed(db: Session, *, entries: int, chunks_per_entry: int, marker: str) -> float:
    source_id = _native_source_id(db)
    started = time.perf_counter()
    for index in range(entries):
        body = "\n".join(
            f"benchmark chunk {index}-{chunk_index} token-{marker}"
            for chunk_index in range(chunks_per_entry)
        )
        _insert_raw(
            db,
            source_id=source_id,
            title=f"Benchmark {marker} {index}",
            body=f"{marker}\n{body}",
        )
    return round((time.perf_counter() - started) * 1000, 2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", type=int, default=500, help="fixture Entries to seed")
    parser.add_argument("--chunks-per-entry", type=int, default=4, help="text blocks per fixture Entry")
    parser.add_argument("--samples", type=int, default=20, help="timed samples per operation")
    parser.add_argument(
        "--embedding-entries",
        type=int,
        default=200,
        help="how many fixture Entries get real chunks + FastEmbed vectors (0 disables semantic path)",
    )
    parser.add_argument("--json", type=Path, default=None, help="write results as JSON too")
    parser.add_argument("--keep", action="store_true", help="keep fixtures (default: remove them)")
    args = parser.parse_args()
    if args.entries < 1 or args.chunks_per_entry < 1 or args.samples < 1:
        raise SystemExit("entries, chunks-per-entry and samples must be positive")

    marker = f"bench-{uuid4()}"
    entry_ids: list[UUID] = []
    try:
        with SessionLocal() as db:
            seed_ms = _seed(
                db, entries=args.entries, chunks_per_entry=args.chunks_per_entry, marker=marker
            )
            entry_ids = list(
                db.scalars(select(Entry.id).where(Entry.title.like(f"Benchmark {marker}%"))).all()
            )
            embeddings = 0
            if args.embedding_entries > 0:
                embeddings = _embed_subset(
                    db, entry_ids=entry_ids, limit=min(args.embedding_entries, len(entry_ids))
                )
            raw_counter = iter(range(10_000_000))
            source_id = _native_source_id(db)
            measurements = [
                _measure(
                    "raw_save",
                    args.samples,
                    lambda: _insert_raw(
                        db,
                        source_id=source_id,
                        title=f"Benchmark {marker} save {next(raw_counter)}",
                        body=f"{marker} raw save payload",
                    ),
                ),
                _measure(
                    "fts",
                    args.samples,
                    lambda: search(db, marker, mode="fulltext", limit=30),
                ),
                _measure(
                    "hybrid",
                    args.samples,
                    lambda: search(db, marker, mode="hybrid", limit=30),
                ),
                _measure(
                    "ask_local",
                    args.samples,
                    lambda: ask(db, AskRequest(query=f"{marker} 是什么？", limit=10)),
                ),
            ]
        results = {
            "started_at": datetime.now(UTC).isoformat(),
            "marker": marker,
            "entries": args.entries,
            "chunks_per_entry": args.chunks_per_entry,
            "seed_ms": seed_ms,
            "database": {
                "entries_total": len(entry_ids),
                "embedded_chunks": embeddings,
            },
            "measurements": measurements,
        }
        print(json.dumps(results, ensure_ascii=False, indent=2))
        if args.json:
            args.json.write_text(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    finally:
        if not args.keep:
            with SessionLocal() as db:
                db.execute(delete(Entry).where(Entry.title.like(f"Benchmark {marker}%")))
                db.execute(delete(Entry).where(Entry.raw_content.like(f"{marker}%", escape="\\")))
                db.commit()


if __name__ == "__main__":
    raise SystemExit(main())
