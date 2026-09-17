"""Source-grounded Ask/RAG orchestration."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import ContentUnit, Entry, Memory, MemorySource, Source
from app.prompting import PromptValidationError, resolve_prompt, validate_output
from app.providers import (
    ProviderRequestError,
    ProviderUnavailable,
    get_chat_provider,
    task_messages,
)
from app.routing import task_route
from app.schemas import AskOut, AskRequest, AskSource, SearchResult
from app.secret_scanner import redact_secrets
from app.services.search import extract_identifiers, search

_STOP_WORDS = {
    "我的",
    "我",
    "有没有",
    "哪个",
    "多少",
    "设置",
    "最后",
    "之前",
    "那个",
    "问题",
    "的",
    "是",
    "what",
    "is",
    "the",
    "my",
}


def understand_query(query: str) -> dict[str, Any]:
    tokens = re.findall(r"[A-Za-z0-9_./:-]+|[\u4e00-\u9fff]{2,}", query)
    identifiers = extract_identifiers(query)
    keywords = list(
        dict.fromkeys(
            token
            for token in tokens
            if token.casefold() not in _STOP_WORDS and token not in identifiers
        )
    )
    keywords = identifiers + keywords
    lowered = query.casefold()
    if any(term in lowered for term in ("故障", "问题", "报错", "error", "怎么解决")):
        intent = "troubleshooting_recall"
    elif any(term in lowered for term in ("什么时候", "哪天", "何时")):
        intent = "temporal_recall"
    elif any(term in lowered for term in ("多少", "什么", "当前", "现在", "最后")):
        intent = "fact_recall"
    else:
        intent = "search_recall"
    if any(term in lowered for term in ("第一次", "最早")):
        time_hint = "first"
    elif any(term in lowered for term in ("最近一次", "最新", "最后")):
        time_hint = "latest"
    elif any(
        term in lowered
        for term in ("去年", "上个月", "最近", "前段时间", "前几天", "昨天", "上周", "本周")
    ):
        time_hint = "recent_past"
    else:
        time_hint = None
    answer_mode = "timeline" if time_hint in {"first", "latest", "recent_past"} else "fact"
    return {
        "intent": intent,
        "keywords": keywords[:32],
        "identifiers": identifiers[:32],
        "entities": identifiers[:32],
        "time_hint": time_hint,
        "answer_mode": answer_mode,
    }


def temporal_bounds(
    query: str, now: datetime | None = None
) -> tuple[datetime | None, datetime | None]:
    now = now or datetime.now(UTC)
    lowered = query.casefold()
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if "今天" in lowered:
        return start_of_today, None
    if "昨天" in lowered:
        return start_of_today - timedelta(days=1), start_of_today
    if "最近" in lowered or "前几天" in lowered:
        return now - timedelta(days=30), None
    if "前段时间" in lowered:
        return now - timedelta(days=90), None
    if "上周" in lowered:
        start_of_week = start_of_today - timedelta(days=start_of_today.weekday())
        return start_of_week - timedelta(days=7), start_of_week
    if "本周" in lowered:
        start_of_week = start_of_today - timedelta(days=start_of_today.weekday())
        return start_of_week, None
    if "上个月" in lowered:
        first_this_month = start_of_today.replace(day=1)
        previous_month_end = first_this_month - timedelta(microseconds=1)
        return previous_month_end.replace(day=1), first_this_month
    if "去年" in lowered:
        start = start_of_today.replace(year=now.year - 1, month=1, day=1)
        return start, start.replace(year=now.year)
    month_match = re.search(r"(1[0-2]|[1-9])月(?:份)?", query)
    if month_match:
        month = int(month_match.group(1))
        year = now.year if month <= now.month else now.year - 1
        start = start_of_today.replace(year=year, month=month, day=1)
        end_month = 12 if month == 12 else month + 1
        end_year = year + 1 if month == 12 else year
        return start, start.replace(year=end_year, month=end_month)
    return None, None


def _memory_sources(
    db: Session,
    query: str,
    *,
    source_scope: str,
    source_id,
    limit: int,
) -> list[SearchResult]:
    understanding = understand_query(query)
    terms = understanding["keywords"]
    statement = (
        select(Memory, MemorySource, ContentUnit, Source, Entry)
        .join(MemorySource, MemorySource.memory_id == Memory.id)
        .join(ContentUnit, ContentUnit.id == MemorySource.content_unit_id)
        .join(Source, Source.id == ContentUnit.source_id)
        .outerjoin(Entry, Entry.id == MemorySource.entry_id)
        .where(Memory.status == "active", or_(Entry.id.is_(None), Entry.deleted_at.is_(None)))
    )
    if terms:
        conditions = []
        for term in terms:
            pattern = f"%{term}%"
            conditions.extend(
                (Memory.subject_key.ilike(pattern), Memory.memory_text.ilike(pattern))
            )
        statement = statement.where(or_(*conditions))
    if source_scope == "native":
        statement = statement.where(Source.is_native.is_(True))
    elif source_scope == "external":
        statement = statement.where(Source.is_native.is_(False))
    if source_id:
        statement = statement.where(Source.id == source_id)
    rows = db.execute(
        statement.order_by(Memory.confidence.desc(), Memory.updated_at.desc()).limit(limit)
    ).all()
    results: list[SearchResult] = []
    seen: set[object] = set()
    for memory, _, unit, source, entry in rows:
        if unit.id in seen:
            continue
        seen.add(unit.id)
        results.append(
            SearchResult(
                entry_id=entry.id if entry else None,
                content_unit_id=unit.id,
                attachment_id=unit.attachment_id,
                page_number=(unit.metadata_json or {}).get("page_number"),
                provenance_type=unit.unit_type,
                source_uri=entry.source_uri
                if entry
                else (unit.metadata_json or {}).get("original_url"),
                final_url=(unit.metadata_json or {}).get("final_url"),
                source_id=source.id,
                source_name=source.name,
                source_type=source.source_type,
                created_at=entry.created_at if entry else unit.created_at,
                snippet=memory.memory_text,
                score=memory.confidence,
                match_reason="Active memory",
                exact_match=False,
            )
        )
    return results


def _ask_source(result: SearchResult) -> AskSource:
    return AskSource(
        entry_id=result.entry_id,
        content_unit_id=result.content_unit_id,
        chunk_id=result.chunk_id,
        attachment_id=result.attachment_id,
        page_number=result.page_number,
        provenance_type=result.provenance_type,
        source_uri=result.source_uri,
        final_url=result.final_url,
        source_id=result.source_id,
        source_name=result.source_name,
        source_type=result.source_type,
        external_item_id=result.external_item_id,
        external_id=result.external_id,
        external_url=result.external_url,
        external_created_at=result.external_created_at,
        imported_at=result.imported_at,
        created_at=result.created_at,
        snippet=result.snippet,
        score=result.score,
        jump_target=f"/entries/{result.entry_id}" if result.entry_id else None,
    )


def _strip_mark(text: str) -> str:
    return text.replace("<mark>", "").replace("</mark>", "")


def ask(db: Session, payload: AskRequest) -> AskOut:
    understanding = understand_query(payload.query)
    start, end = temporal_bounds(payload.query)
    retrieval_query = " ".join(understanding["keywords"]) or payload.query
    outcome = search(
        db,
        retrieval_query,
        mode="hybrid",
        limit=payload.limit,
        source_scope=payload.source_scope,
        source_id=payload.source_id,
        start=start,
        end=end,
    )
    memory_results = _memory_sources(
        db,
        payload.query,
        source_scope=payload.source_scope,
        source_id=payload.source_id,
        limit=payload.limit,
    )
    result_by_unit = {item.content_unit_id: item for item in memory_results}
    for item in outcome.items:
        result_by_unit.setdefault(item.content_unit_id, item)
    results = list(result_by_unit.values())
    if understanding["time_hint"] == "latest":
        results.sort(
            key=lambda item: item.created_at or datetime.min.replace(tzinfo=UTC), reverse=True
        )
    elif understanding["time_hint"] == "first":
        results.sort(key=lambda item: item.created_at or datetime.max.replace(tzinfo=UTC))
    results = results[: payload.limit]
    sources = [_ask_source(result) for result in results]
    settings = get_settings()
    chat_available = bool(settings.chat_base_url and settings.chat_api_key)
    answer = "没有找到可靠来源，不能给出确定结论。"
    confidence = 0.0
    is_inference = False
    if sources:
        context = "\n\n".join(
            f"[{index}] {source.source_name} {source.created_at}\n"
            f"{redact_secrets(_strip_mark(source.snippet))[:900]}"
            for index, source in enumerate(sources, start=1)
        )
        if chat_available:
            try:
                resolved = resolve_prompt(
                    db,
                    "answer",
                    {"question": payload.query, "sources": context},
                )
                provider_name, model = task_route(db, "chat", resolved)
                chat_available = bool(
                    settings.chat_base_url
                    and settings.chat_api_key
                    and (model or settings.chat_model)
                )
                if not chat_available:
                    raise ProviderUnavailable("Chat provider is not configured")
                response = get_chat_provider(
                    model_override=model,
                    provider_override=provider_name,
                ).complete(
                    task_messages(
                        redact_secrets(resolved.content),
                        user_prompt="请依据上述来源回答问题，并按 Output Schema 输出 JSON。",
                    ),
                    max_tokens=800,
                    temperature=0.0,
                    json_mode=True,
                )
                generated = validate_output("answer", response.content)
                answer = generated.answer
                confidence = min(1.0, max(0.0, generated.confidence))
                is_inference = generated.is_inference
            except (PromptValidationError, ProviderUnavailable, ProviderRequestError):
                chat_available = False
        if not chat_available:
            answer = "根据已保存的来源：\n" + "\n".join(
                f"- {_strip_mark(source.snippet)}" for source in sources[:3]
            )
            confidence = min(0.9, max(source.score for source in sources))
    return AskOut(
        answer=answer,
        confidence=round(confidence, 5),
        is_inference=is_inference,
        sources=sources,
        semantic_available=outcome.semantic_available,
        query_understanding=understanding,
        chat_available=chat_available,
        filtered_low_relevance=outcome.filtered_low_relevance,
    )
