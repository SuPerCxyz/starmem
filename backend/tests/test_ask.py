from types import SimpleNamespace
from uuid import uuid4

import app.ask as ask_module
from app.ask import ask, temporal_bounds, understand_query
from app.schemas import AskRequest, SearchResult
from app.services.search import SearchOutcome


def test_query_understanding_and_temporal_preset():
    understood = understand_query("我前段时间遇到 node-3903 的 multipath 问题")
    assert understood["intent"] == "troubleshooting_recall"
    assert "node-3903" in understood["identifiers"]
    assert understood["time_hint"] == "recent_past"
    start, end = temporal_bounds("上个月")
    assert start and end and start < end


def _offline_chat(monkeypatch):
    """单元测试不依赖外部 Chat 配置，强制走确定性摘要路径。"""
    monkeypatch.setattr(
        ask_module, "get_settings", lambda: SimpleNamespace(chat_base_url="", chat_api_key="")
    )


def test_ask_is_source_grounded_and_refuses_without_sources(monkeypatch):
    _offline_chat(monkeypatch)
    result = SearchResult(
        entry_id=uuid4(),
        content_unit_id=uuid4(),
        source_id=uuid4(),
        source_name="StarMem Native",
        source_type="native",
        created_at=None,
        snippet="V100 当前长期功耗限制为 150W。",
        score=0.95,
        match_reason="Full-text match",
        exact_match=False,
    )
    import app.ask as ask_module

    monkeypatch.setattr(
        ask_module, "search", lambda *args, **kwargs: SearchOutcome([result], False)
    )
    monkeypatch.setattr(ask_module, "_memory_sources", lambda *args, **kwargs: [])
    grounded = ask(None, AskRequest(query="V100 功耗多少？"))
    assert "150W" in grounded.answer
    assert grounded.sources[0].entry_id == result.entry_id
    assert grounded.sources[0].jump_target == f"/entries/{result.entry_id}"

    monkeypatch.setattr(ask_module, "search", lambda *args, **kwargs: SearchOutcome([], False))
    refused = ask(None, AskRequest(query="没有记录的事实"))
    assert refused.sources == []
    assert "不能给出确定结论" in refused.answer
    assert refused.confidence == 0


def test_ask_surfaces_filtered_low_relevance(monkeypatch):
    _offline_chat(monkeypatch)
    result = SearchResult(
        entry_id=uuid4(),
        content_unit_id=uuid4(),
        source_id=uuid4(),
        source_name="StarMem Native",
        source_type="native",
        created_at=None,
        snippet="openstack volume create --size 10",
        score=0.26,
        match_reason="Hybrid match",
        exact_match=False,
    )
    import app.ask as ask_module

    monkeypatch.setattr(
        ask_module, "search", lambda *args, **kwargs: SearchOutcome([result], True, 2)
    )
    monkeypatch.setattr(ask_module, "_memory_sources", lambda *args, **kwargs: [])
    grounded = ask(None, AskRequest(query="创建云盘命令"))
    assert grounded.filtered_low_relevance == 2
    assert grounded.sources[0].entry_id == result.entry_id
    assert grounded.confidence == round(0.26, 5)
