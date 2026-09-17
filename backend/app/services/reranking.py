"""Optional reranking of Hybrid candidates with safe fallback."""

from __future__ import annotations

import time

import httpx

from app.config import get_settings
from app.metrics import observe
from app.schemas import SearchResult

RERANK_CANDIDATES = 30


def rerank_results(query: str, items: list[SearchResult]) -> list[SearchResult]:
    settings = get_settings()
    provider = (getattr(settings, "reranker_provider", "") or "").strip().lower()
    if provider in {"", "none", "disabled"} or len(items) < 2:
        return items
    base_url = (getattr(settings, "reranker_base_url", "") or "").strip()
    model = (getattr(settings, "reranker_model", "") or "").strip()
    if not base_url or not model:
        return items
    documents = [item.snippet.replace("<mark>", "").replace("</mark>", "") for item in items]
    started = time.perf_counter()
    try:
        response = httpx.post(
            f"{base_url.rstrip('/')}/rerank",
            json={"model": model, "query": query, "documents": documents},
            timeout=getattr(settings, "reranker_timeout_seconds", 10),
        )
        response.raise_for_status()
        payload = response.json()
        raw_scores = payload.get("results") or payload.get("scores") or []
        if not raw_scores:
            raise ValueError("Reranker returned no scores")
        scores: list[float] = [0.0] * len(items)
        for position, entry in enumerate(raw_scores):
            if isinstance(entry, dict):
                index = entry.get("index")
                score = float(entry.get("relevance_score") or entry.get("score") or 0.0)
                target = index if isinstance(index, int) and 0 <= index < len(items) else position
                scores[target] = score
            else:
                scores[position] = float(entry)
        if len(scores) != len(items):
            raise ValueError("Reranker result count mismatch")
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        observe("search.rerank", latency_ms=round((time.perf_counter() - started) * 1000))
        return items
    observe("search.rerank", latency_ms=round((time.perf_counter() - started) * 1000))
    ranked = sorted(zip(items, scores, strict=True), key=lambda pair: pair[1], reverse=True)
    return [
        item.model_copy(update={"score": round(float(score), 5), "match_reason": "Hybrid + Rerank"})
        for item, score in ranked
    ]
