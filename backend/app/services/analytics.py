"""Redacted, bounded Ask query analytics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AskQuery
from app.schemas import WorkbenchItemOut
from app.secret_scanner import redact_secrets

MAX_QUERY_LENGTH = 500
MAX_AGGREGATED_QUERIES = 100
FREQUENT_WINDOW_DAYS = 30


def record_query(
    db: Session,
    *,
    query: str,
    source_scope: str,
    result_count: int,
    latency_ms: int | None,
) -> None:
    redacted = " ".join(redact_secrets(query).split())[:MAX_QUERY_LENGTH]
    if not redacted:
        return
    db.add(
        AskQuery(
            query_text=redacted,
            source_scope=source_scope,
            result_count=max(0, result_count),
            latency_ms=latency_ms,
        )
    )
    db.commit()


def frequent_queries(db: Session, *, limit: int = 50) -> list[WorkbenchItemOut]:
    cutoff = datetime.now(UTC) - timedelta(days=FREQUENT_WINDOW_DAYS)
    normalized = func.lower(func.btrim(AskQuery.query_text))
    rows = db.execute(
        select(
            normalized.label("query_text"),
            func.count().label("hits"),
            func.max(AskQuery.created_at).label("last_asked"),
        )
        .where(AskQuery.created_at >= cutoff)
        .group_by(normalized)
        .order_by(func.count().desc(), func.max(AskQuery.created_at).desc())
        .limit(min(max(1, limit), MAX_AGGREGATED_QUERIES))
    ).all()
    return [
        WorkbenchItemOut(
            id=uuid5(NAMESPACE_URL, f"starmem-ask-query:{row.query_text}"),
            kind="frequent-query",
            title=row.query_text,
            status=str(row.hits),
            detail=f"最近 {FREQUENT_WINDOW_DAYS} 天询问 {row.hits} 次",
            created_at=row.last_asked,
        )
        for row in rows
    ]
