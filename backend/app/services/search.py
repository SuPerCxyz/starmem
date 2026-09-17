from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    ContentUnit,
    Entity,
    Entry,
    EntryChunk,
    EntryEntity,
    EntryTag,
    ExternalItem,
    Observation,
    Source,
    Tag,
)
from app.providers import EmbeddingProvider, ProviderUnavailable, get_embedding_provider
from app.schemas import SearchResult
from app.services.reranking import rerank_results

IDENTIFIER_PATTERNS = (
    re.compile(r"^[0-9a-f]{8}-[0-9a-f-]{27}$", re.IGNORECASE),
    re.compile(r"^(?:naa\.)?[0-9a-f]{16,}$", re.IGNORECASE),
    re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$"),
    re.compile(r"^(?:https?://)?[a-z0-9][a-z0-9.-]+\.[a-z]{2,}$", re.IGNORECASE),
    re.compile(r"^(?:node|host|srv|vm|www)[-_][a-z0-9.-]+$", re.IGNORECASE),
    re.compile(r"^[a-z][a-z0-9]+(?:[-_][a-z0-9]+)+$", re.IGNORECASE),
    re.compile(r"^(?:[0-9a-f]{1,4}:){2,}[0-9a-f:]{1,4}$", re.IGNORECASE),
    re.compile(r"^/[-\w./]+$"),
    re.compile(r"^(?:e|err|error|http)[-_]?\d{3,5}$", re.IGNORECASE),
)


@dataclass(frozen=True)
class SearchOutcome:
    items: list[SearchResult]
    semantic_available: bool
    filtered_low_relevance: int = 0


CJK_RUN_PATTERN = re.compile(r"[\u4e00-\u9fff]+")
LATIN_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_./:-]{2,}")
MAX_QUERY_TERMS = 24


def _like_pattern(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def query_terms(query: str) -> list[str]:
    """把查询切成可用于字面匹配的 token：中文 bigram + 拉丁词，保序去重。"""
    terms: list[str] = []
    for run in CJK_RUN_PATTERN.findall(query):
        if len(run) < 2:
            terms.append(run)
            continue
        terms.extend(run[index : index + 2] for index in range(len(run) - 1))
    terms.extend(LATIN_TOKEN_PATTERN.findall(query))
    return list(dict.fromkeys(terms))[:MAX_QUERY_TERMS]


def _best_scores(items: list[SearchResult]) -> dict[UUID, float]:
    scores: dict[UUID, float] = {}
    for item in items:
        scores[item.content_unit_id] = max(scores.get(item.content_unit_id, 0.0), item.score)
    return scores


def _filter_low_similarity(
    keyword_items: list[SearchResult],
    semantic_items: list[SearchResult],
    *,
    minimum: float,
) -> tuple[list[SearchResult], int]:
    """丢弃既没有关键词字面命中、语义相似度又低于阈值的候选。"""
    keyword_units = {item.content_unit_id for item in keyword_items}
    kept: list[SearchResult] = []
    dropped: set[UUID] = set()
    for item in semantic_items:
        if item.content_unit_id in keyword_units or item.score >= minimum:
            kept.append(item)
        else:
            dropped.add(item.content_unit_id)
    return kept, len(dropped)


def extract_identifiers(query: str) -> list[str]:
    values: list[str] = []
    for token in re.findall(r"[^\s,;，。；]+", query.strip()):
        if any(pattern.fullmatch(token) for pattern in IDENTIFIER_PATTERNS):
            values.append(token)
    return values


def is_exact_identifier(query: str) -> bool:
    query = query.strip()
    return bool(query and any(pattern.fullmatch(query) for pattern in IDENTIFIER_PATTERNS))


def _highlight(content: str, query: str) -> str:
    normalized = content.replace("\n", " ")
    position = normalized.lower().find(query.lower())
    if position < 0:
        return normalized[:260]
    start = max(0, position - 90)
    end = min(len(normalized), position + len(query) + 150)
    fragment = normalized[start:end]
    return re.sub(
        re.escape(query),
        lambda match: f"<mark>{match.group(0)}</mark>",
        fragment,
        flags=re.IGNORECASE,
    )


def _attachment_provenance(unit: ContentUnit) -> dict[str, object]:
    metadata = unit.metadata_json or {}
    page_number = metadata.get("page_number")
    return {
        "attachment_id": unit.attachment_id,
        "page_number": page_number if isinstance(page_number, int) else None,
        "provenance_type": unit.unit_type,
    }


def _native_provenance(entry: Entry | None, unit: ContentUnit) -> dict[str, object]:
    metadata = unit.metadata_json or {}
    return {
        "source_uri": entry.source_uri if entry else metadata.get("original_url"),
        "final_url": metadata.get("final_url"),
    }


def _apply_source_filters(
    statement,
    *,
    source_scope: str,
    source_id: UUID | None,
    start: datetime | None,
    end: datetime | None,
):
    if source_scope == "native":
        statement = statement.where(Source.is_native.is_(True))
    elif source_scope == "external":
        statement = statement.where(Source.is_native.is_(False))
    if source_id:
        statement = statement.where(Source.id == source_id)
    if start:
        statement = statement.where(ContentUnit.created_at >= start)
    if end:
        statement = statement.where(ContentUnit.created_at <= end)
    return statement


def _apply_entry_filters(
    statement,
    *,
    content_type: str | None,
    tag: str | None,
    entity: str | None,
    project: str | None,
    topic: str | None,
):
    if content_type:
        # Match either the primary type or any type in the multi-classification set.
        statement = statement.where(
            or_(
                Entry.content_type == content_type,
                Entry.content_types.contains([content_type]),
            )
        )
    if tag:
        statement = statement.where(
            select(EntryTag.entry_id)
            .join(Tag, Tag.id == EntryTag.tag_id)
            .where(EntryTag.entry_id == Entry.id, Tag.normalized_name == tag.casefold())
            .exists()
        )
    if entity:
        statement = statement.where(
            select(EntryEntity.entry_id)
            .join(Entity, Entity.id == EntryEntity.entity_id)
            .where(EntryEntity.entry_id == Entry.id, Entity.normalized_name == entity.casefold())
            .exists()
        )
    for observation_type, value in (("project", project), ("topic", topic)):
        if value:
            statement = statement.where(
                select(Observation.id)
                .where(
                    Observation.entry_id == Entry.id,
                    Observation.observation_type == observation_type,
                    Observation.data_json["name"].as_string() == value,
                )
                .exists()
            )
    return statement


def search_fulltext(
    db: Session,
    query: str,
    *,
    limit: int = 30,
    source_scope: str = "all",
    source_id: UUID | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    content_type: str | None = None,
    tag: str | None = None,
    entity: str | None = None,
    project: str | None = None,
    topic: str | None = None,
) -> list[SearchResult]:
    exact = is_exact_identifier(query)
    rank = func.ts_rank_cd(ContentUnit.fts_vector, func.websearch_to_tsquery("simple", query))
    trigram = func.similarity(ContentUnit.content, query)
    match_conditions = [
        ContentUnit.fts_vector.op("@@")(func.websearch_to_tsquery("simple", query)),
        ContentUnit.content.ilike(_like_pattern(query), escape="\\"),
    ]
    match_conditions.extend(
        ContentUnit.content.ilike(_like_pattern(term), escape="\\") for term in query_terms(query)
    )
    statement = (
        select(
            ContentUnit, Entry, Source, ExternalItem, rank.label("rank"), trigram.label("trigram")
        )
        .join(Source, Source.id == ContentUnit.source_id)
        .outerjoin(Entry, Entry.id == ContentUnit.entry_id)
        .outerjoin(ExternalItem, ExternalItem.id == ContentUnit.external_item_id)
        .where(
            or_(*match_conditions),
            or_(Entry.id.is_(None), Entry.deleted_at.is_(None)),
        )
    )
    statement = _apply_source_filters(
        statement,
        source_scope=source_scope,
        source_id=source_id,
        start=start,
        end=end,
    )
    statement = _apply_entry_filters(
        statement,
        content_type=content_type,
        tag=tag,
        entity=entity,
        project=project,
        topic=topic,
    )
    rows = db.execute(statement.order_by(rank.desc(), trigram.desc()).limit(limit)).all()
    results: list[SearchResult] = []
    for unit, entry, source, external, raw_rank, raw_trigram in rows:
        contains_exact = query.lower() in unit.content.lower()
        score = float(raw_rank or 0) + float(raw_trigram or 0)
        if exact and contains_exact:
            score += 100.0
        results.append(
            SearchResult(
                entry_id=entry.id if entry else None,
                content_unit_id=unit.id,
                **_attachment_provenance(unit),
                **_native_provenance(entry, unit),
                source_id=source.id,
                source_name=source.name,
                source_type=source.source_type,
                external_item_id=external.id if external else None,
                external_id=external.external_id if external else None,
                external_url=(external.metadata_json or {}).get("url") if external else None,
                external_created_at=external.external_created_at if external else None,
                imported_at=unit.created_at,
                created_at=entry.created_at if entry else unit.created_at,
                snippet=_highlight(unit.content, query),
                score=round(score, 5),
                match_reason="Exact match" if exact and contains_exact else "Full-text match",
                exact_match=exact and contains_exact,
            )
        )
    return sorted(results, key=lambda item: item.score, reverse=True)


def search_semantic(
    db: Session,
    query: str,
    *,
    limit: int = 30,
    source_scope: str = "all",
    source_id: UUID | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    provider: EmbeddingProvider | None = None,
    content_type: str | None = None,
    tag: str | None = None,
    entity: str | None = None,
    project: str | None = None,
    topic: str | None = None,
) -> tuple[list[SearchResult], bool]:
    try:
        provider = provider or get_embedding_provider()
        if provider is None:
            return [], False
        vector = provider.embed([query])[0]
    except (ProviderUnavailable, IndexError):
        return [], False

    distance = EntryChunk.embedding.cosine_distance(vector).label("distance")
    statement = (
        select(EntryChunk, ContentUnit, Entry, Source, ExternalItem, distance)
        .join(ContentUnit, ContentUnit.id == EntryChunk.content_unit_id)
        .join(Source, Source.id == ContentUnit.source_id)
        .outerjoin(Entry, Entry.id == EntryChunk.entry_id)
        .outerjoin(ExternalItem, ExternalItem.id == ContentUnit.external_item_id)
        .where(
            EntryChunk.embedding.is_not(None),
            or_(Entry.id.is_(None), Entry.deleted_at.is_(None)),
        )
    )
    statement = _apply_source_filters(
        statement,
        source_scope=source_scope,
        source_id=source_id,
        start=start,
        end=end,
    )
    statement = _apply_entry_filters(
        statement,
        content_type=content_type,
        tag=tag,
        entity=entity,
        project=project,
        topic=topic,
    )
    rows = db.execute(statement.order_by(distance.asc()).limit(limit)).all()
    results: list[SearchResult] = []
    for chunk, unit, entry, source, external, raw_distance in rows:
        similarity = max(0.0, min(1.0, 1.0 - float(raw_distance or 1.0)))
        results.append(
            SearchResult(
                entry_id=entry.id if entry else None,
                content_unit_id=unit.id,
                chunk_id=chunk.id,
                **_attachment_provenance(unit),
                **_native_provenance(entry, unit),
                source_id=source.id,
                source_name=source.name,
                source_type=source.source_type,
                external_item_id=external.id if external else None,
                external_id=external.external_id if external else None,
                external_url=(external.metadata_json or {}).get("url") if external else None,
                external_created_at=external.external_created_at if external else None,
                imported_at=unit.created_at,
                created_at=entry.created_at if entry else unit.created_at,
                snippet=_highlight(chunk.content, query),
                score=round(similarity, 5),
                match_reason="Semantic match",
                exact_match=bool(extract_identifiers(query))
                and query.lower() in chunk.content.lower(),
            )
        )
    return results, True


def _hybrid(
    keyword_items: list[SearchResult],
    semantic_items: list[SearchResult],
    *,
    query: str,
    limit: int,
) -> list[SearchResult]:
    settings = get_settings()
    keyword_scores = _best_scores(keyword_items)
    semantic_scores = _best_scores(semantic_items)
    by_unit: dict[UUID, SearchResult] = {}
    for item in keyword_items + semantic_items:
        current = by_unit.get(item.content_unit_id)
        if current is None or item.score > current.score or item.exact_match:
            by_unit[item.content_unit_id] = item
    exact_query = is_exact_identifier(query)
    results: list[SearchResult] = []
    for unit_id, item in by_unit.items():
        exact = any(
            candidate.content_unit_id == unit_id and candidate.exact_match
            for candidate in keyword_items + semantic_items
        )
        score = settings.hybrid_keyword_weight * keyword_scores.get(
            unit_id, 0.0
        ) + settings.hybrid_semantic_weight * semantic_scores.get(unit_id, 0.0)
        if exact_query and exact:
            score += 1.0
        results.append(
            item.model_copy(
                update={
                    "score": round(score, 5),
                    "match_reason": "Exact match" if exact else "Hybrid match",
                    "exact_match": exact,
                }
            )
        )
    return sorted(results, key=lambda result: result.score, reverse=True)[:limit]


def search(
    db: Session,
    query: str,
    *,
    mode: str = "hybrid",
    limit: int = 30,
    source_scope: str = "all",
    source_id: UUID | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    content_type: str | None = None,
    tag: str | None = None,
    entity: str | None = None,
    project: str | None = None,
    topic: str | None = None,
) -> SearchOutcome:
    keyword_items = search_fulltext(
        db,
        query,
        limit=max(limit * 3, 30),
        source_scope=source_scope,
        source_id=source_id,
        start=start,
        end=end,
        content_type=content_type,
        tag=tag,
        entity=entity,
        project=project,
        topic=topic,
    )
    if mode == "fulltext":
        return SearchOutcome(keyword_items[:limit], False)
    semantic_items, available = search_semantic(
        db,
        query,
        limit=max(limit * 3, 30),
        source_scope=source_scope,
        source_id=source_id,
        start=start,
        end=end,
        content_type=content_type,
        tag=tag,
        entity=entity,
        project=project,
        topic=topic,
    )
    if not available:
        return SearchOutcome(keyword_items[:limit], False)
    minimum = get_settings().semantic_min_similarity
    if mode == "semantic":
        semantic_only, filtered = _filter_low_similarity([], semantic_items, minimum=minimum)
        return SearchOutcome(semantic_only[:limit], True, filtered)
    semantic_items, filtered = _filter_low_similarity(
        keyword_items, semantic_items, minimum=minimum
    )
    items = _hybrid(keyword_items, semantic_items, query=query, limit=limit)
    items = rerank_results(query, items)
    return SearchOutcome(items, True, filtered)
