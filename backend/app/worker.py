import logging
import time
from uuid import UUID

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from sqlalchemy import select

from app.ai_tasks import run_ai_job
from app.config import get_settings
from app.db import SessionLocal
from app.logging import configure_logging
from app.memory_engine import apply_candidate
from app.metrics import observe
from app.models import AIJob, Attachment, Entry, EntryChunk, MemoryCandidate, Observation
from app.providers import (
    ProviderUnavailable,
    get_embedding_provider,
    get_image_description_provider,
)
from app.services.embeddings import rebuild_chunks, timed_embed
from app.services.ingestion import process_job as process_ingestion_job

configure_logging()
settings = get_settings()
broker = RedisBroker(url=settings.redis_url)
dramatiq.set_broker(broker)
logger = logging.getLogger(__name__)


@dramatiq.actor(max_retries=2, min_backoff=1_000)
def process_entry(entry_id: str) -> None:
    """Run the provider-independent indexing steps and optional embeddings."""
    with SessionLocal() as db:
        entry = db.get(Entry, entry_id)
        if not entry or entry.deleted_at:
            return
        generation = entry.ai_generation
        _run_chunk_job(db, entry, generation)
        _run_embedding_job(db, entry, generation)
        for job_type in (
            "classify",
            "summarize",
            "tag",
            "entity_extract",
            "time_extract",
            "project_classify",
            "topic_classify",
            "memory_extract",
            "relation_build",
        ):
            job = _job(db, entry, job_type, generation)
            if job:
                run_ai_job(db, entry, job)
        _run_image_description_job(db, entry, generation)
        for candidate in db.scalars(
            select(MemoryCandidate).where(
                MemoryCandidate.entry_id == entry.id,
                MemoryCandidate.generation == generation,
                MemoryCandidate.status == "pending",
            )
        ).all():
            try:
                apply_candidate(db, candidate)
            except Exception as exc:
                db.rollback()
                candidate = db.get(MemoryCandidate, candidate.id)
                if candidate:
                    candidate.status = "failed"
                    db.commit()
                logger.warning(
                    "memory candidate apply failed",
                    extra={"entry_id": entry_id, "error_type": type(exc).__name__},
                )
        statuses = db.scalars(
            select(AIJob.status).where(AIJob.entry_id == entry.id, AIJob.generation == generation)
        ).all()
        entry.ai_status = (
            "ready"
            if statuses and all(status in {"done", "skipped"} for status in statuses)
            else "partial"
        )
        db.commit()
        logger.info("entry indexed", extra={"entry_id": entry_id})


@dramatiq.actor(max_retries=2, min_backoff=1_000)
def process_ingestion(job_id: str) -> None:
    """Fetch or parse one native import, then enqueue the normal Entry pipeline."""
    started = time.perf_counter()
    with SessionLocal() as db:
        entry_id = process_ingestion_job(db, UUID(job_id))
    observe("job.import", latency_ms=round((time.perf_counter() - started) * 1000))
    if entry_id:
        try:
            process_entry.send(str(entry_id))
        except Exception as exc:
            logger.warning(
                "import completed but entry queue unavailable",
                extra={
                    "job_id": job_id,
                    "entry_id": str(entry_id),
                    "error_type": type(exc).__name__,
                },
            )


def _job(db, entry: Entry, job_type: str, generation: int) -> AIJob | None:
    return db.scalar(
        select(AIJob).where(
            AIJob.entry_id == entry.id,
            AIJob.job_type == job_type,
            AIJob.generation == generation,
        )
    )


def _start_job(db, job: AIJob) -> None:
    job.status = "running"
    job.attempt += 1
    job.started_at = time_to_utc()
    job.error = None
    db.commit()


def _finish_job(db, job: AIJob, *, status: str, started: float, error: str | None = None) -> None:
    job.status = status
    job.finished_at = time_to_utc()
    job.latency_ms = round((time.perf_counter() - started) * 1000)
    job.error = error
    observe(f"job.{job.job_type}", latency_ms=job.latency_ms)
    db.commit()


def _run_chunk_job(db, entry: Entry, generation: int) -> None:
    job = _job(db, entry, "chunk", generation)
    if not job or job.status == "done":
        return
    _start_job(db, job)
    started = time.perf_counter()
    try:
        rebuild_chunks(db, entry)
        db.commit()
        _finish_job(db, job, status="done", started=started)
    except Exception as exc:
        db.rollback()
        _finish_job(db, job, status="failed", started=started, error=type(exc).__name__)


def _run_embedding_job(db, entry: Entry, generation: int) -> None:
    job = _job(db, entry, "embedding", generation)
    if not job or job.status == "done":
        return
    _start_job(db, job)
    started = time.perf_counter()
    try:
        provider = get_embedding_provider()
        if provider is None:
            raise ProviderUnavailable("Embedding provider is disabled")
        job.provider = provider.name
        job.model = provider.model
        chunks = db.scalars(
            select(EntryChunk)
            .where(EntryChunk.entry_id == entry.id)
            .order_by(EntryChunk.chunk_index)
        ).all()
        vectors, latency_ms = timed_embed(provider, [chunk.content for chunk in chunks])
        for chunk, vector in zip(chunks, vectors, strict=True):
            chunk.embedding = vector
        job.latency_ms = latency_ms
        db.commit()
        _finish_job(db, job, status="done", started=started)
    except ProviderUnavailable as exc:
        db.rollback()
        _finish_job(db, job, status="failed", started=started, error=str(exc)[:500])
    except Exception as exc:
        db.rollback()
        _finish_job(db, job, status="failed", started=started, error=type(exc).__name__)


def _run_image_description_job(db, entry: Entry, generation: int) -> None:
    """Describe image attachments when a vision provider is configured."""
    job = _job(db, entry, "image_describe", generation)
    if not job or job.status == "done":
        return
    attachment = db.scalar(
        select(Attachment)
        .where(Attachment.entry_id == entry.id, Attachment.media_type.like("image/%"))
        .order_by(Attachment.created_at)
    )
    if not attachment:
        _start_job(db, job)
        _finish_job(db, job, status="skipped", started=time.perf_counter(), error=None)
        return
    _start_job(db, job)
    started = time.perf_counter()
    provider = get_image_description_provider()
    if provider is None:
        _finish_job(
            db,
            job,
            status="skipped",
            started=started,
            error="image_description_disabled",
        )
        return
    try:
        from app.storage import read_attachment

        data = read_attachment(attachment.storage_key).read_bytes()
        description = provider.describe(data, media_type=attachment.media_type)
        observation = db.scalar(
            select(Observation).where(
                Observation.entry_id == entry.id,
                Observation.observation_type == "image_description",
                Observation.generation == generation,
            )
        )
        payload = {"description": description, "confidence": 0.7, "is_inference": True}
        if observation:
            observation.data_json = payload
        else:
            db.add(
                Observation(
                    entry_id=entry.id,
                    observation_type="image_description",
                    data_json=payload,
                    source="ai",
                    generation=generation,
                )
            )
        job.provider = provider.name
        job.model = provider.model
        db.commit()
        _finish_job(db, job, status="done", started=started)
    except ProviderUnavailable as exc:
        db.rollback()
        _finish_job(db, job, status="skipped", started=started, error=str(exc)[:500])
    except Exception as exc:
        db.rollback()
        _finish_job(db, job, status="failed", started=started, error=type(exc).__name__)


def time_to_utc():
    from datetime import UTC, datetime

    return datetime.now(UTC)
