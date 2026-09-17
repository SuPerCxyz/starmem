from __future__ import annotations

from uuid import uuid4

from app.schemas import SearchResult
from app.services.search import (
    _filter_low_similarity,
    _hybrid,
    _like_pattern,
    extract_identifiers,
    is_exact_identifier,
    query_terms,
)


def _result(content_unit_id, *, score, exact=False, chunk_id=None):
    return SearchResult(
        entry_id=uuid4(),
        content_unit_id=content_unit_id,
        chunk_id=chunk_id,
        source_id=uuid4(),
        source_name="Fixture",
        source_type="native",
        created_at=None,
        snippet="fixture",
        score=score,
        match_reason="fixture",
        exact_match=exact,
    )


def test_fixed_chinese_paraphrase_and_causal_hybrid_fixture():
    causal = uuid4()
    config = uuid4()
    keyword = [_result(causal, score=0.62), _result(config, score=0.9)]
    semantic = [_result(causal, score=0.98), _result(config, score=0.35)]
    ranked = _hybrid(
        keyword,
        semantic,
        query="multipath undef iscsi",
        limit=5,
    )
    assert ranked[0].content_unit_id == causal


def test_exact_identifier_boost_outranks_semantic_only_candidate():
    exact_unit = uuid4()
    semantic_unit = uuid4()
    ranked = _hybrid(
        [_result(exact_unit, score=0.05, exact=True)],
        [_result(semantic_unit, score=1.0)],
        query="naa.6001405abcdef1234567890abcdef12",
        limit=5,
    )
    assert ranked[0].content_unit_id == exact_unit
    assert ranked[0].exact_match is True


def test_identifier_extraction_and_semantic_fallback_contract(monkeypatch):
    import app.services.search as search_module

    assert is_exact_identifier("naa.6001405abcdef1234567890abcdef12")
    assert "node-3903" in extract_identifiers("node-3903 multipath")
    fallback = _result(uuid4(), score=1.0)
    monkeypatch.setattr(search_module, "search_fulltext", lambda *args, **kwargs: [fallback])
    monkeypatch.setattr(search_module, "search_semantic", lambda *args, **kwargs: ([], False))
    outcome = search_module.search(None, "paraphrase", mode="hybrid", limit=5)
    assert outcome.semantic_available is False
    assert outcome.items == [fallback]


def test_query_terms_splits_chinese_into_bigrams():
    assert query_terms("创建云盘命令") == ["创建", "建云", "云盘", "盘命", "命令"]
    assert query_terms("node_3903 multipath") == ["node_3903", "multipath"]
    assert query_terms("创建 云盘") == ["创建", "云盘"]
    assert query_terms("   ") == []


def test_like_pattern_escapes_wildcards():
    assert _like_pattern("100%") == "%100\\%%"
    assert _like_pattern("node_3903") == "%node\\_3903%"


def test_low_similarity_semantic_candidates_are_filtered():
    keyword_unit = uuid4()
    weak = _result(uuid4(), score=0.24)
    strong = _result(uuid4(), score=0.57)
    keyword_hit = _result(keyword_unit, score=0.05)
    kept, dropped = _filter_low_similarity(
        [_result(keyword_unit, score=0.02)],
        [weak, strong, keyword_hit],
        minimum=0.35,
    )
    assert [item.content_unit_id for item in kept] == [
        strong.content_unit_id,
        keyword_hit.content_unit_id,
    ]
    assert dropped == 1


def test_hybrid_uses_absolute_semantic_score_without_normalisation():
    unit = uuid4()
    ranked = _hybrid([], [_result(unit, score=0.5)], query="任意中文问题", limit=5)
    assert ranked[0].score == round(0.45 * 0.5, 5)
