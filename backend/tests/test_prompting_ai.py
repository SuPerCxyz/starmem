from __future__ import annotations

from uuid import uuid4

import httpx
from sqlalchemy import delete, select

from app.ai_tasks import run_ai_job
from app.db import SessionLocal
from app.models import AiDerivationMeta, AIJob, Entry, Observation, Source
from app.prompting import PromptValidationError, extract_json, run_prompt_tests, validate_output
from app.providers import (
    ChatResult,
    MockChatProvider,
    OpenAICompatibleChatProvider,
    ProviderRequestError,
)


def test_prompt_json_extraction_and_strict_reconcile_operation():
    assert extract_json('prefix ```json\n{"operation": "ADD"}\n``` suffix') == {"operation": "ADD"}
    try:
        validate_output(
            "memory_reconcile",
            '{"operation":"DROP","confidence":1,"reason":"bad"}',
        )
    except PromptValidationError as exc:
        assert "Validation Failed" in str(exc)
    else:
        raise AssertionError("unknown reconcile operations must be rejected")


def test_ai_job_valid_output_persists_provenance_and_invalid_output_does_not():
    entry_id = None
    try:
        with SessionLocal() as db:
            source = db.scalar(select(Source).where(Source.is_native.is_(True)))
            entry = Entry(source_id=source.id, raw_content=f"prompt fixture {uuid4()}")
            db.add(entry)
            db.flush()
            entry_id = entry.id
            valid = AIJob(entry_id=entry.id, job_type="summarize", generation=0)
            invalid = AIJob(entry_id=entry.id, job_type="project_classify", generation=0)
            db.add_all([valid, invalid])
            db.commit()
            assert run_ai_job(
                db,
                entry,
                valid,
                chat_provider=MockChatProvider(
                    '{"summary":"evidence summary","confidence":0.9,"is_inference":false}'
                ),
            )
            assert db.scalar(select(Observation).where(Observation.entry_id == entry.id))
            assert db.scalar(
                select(AiDerivationMeta).where(AiDerivationMeta.object_type == "observation")
            )
            assert not run_ai_job(
                db,
                entry,
                invalid,
                chat_provider=MockChatProvider('{"name":"Project","unexpected":true}'),
            )
            db.refresh(invalid)
            assert invalid.status == "prompt_validation_failed"
            assert (
                db.scalar(
                    select(Observation).where(
                        Observation.entry_id == entry.id, Observation.observation_type == "project"
                    )
                )
                is None
            )
    finally:
        if entry_id:
            with SessionLocal() as db:
                db.execute(delete(Entry).where(Entry.id == entry_id))
                db.commit()


def test_chat_provider_sends_disabled_thinking_and_retries(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs["json"]))
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "model": "qwen35-4b",
                "choices": [{"message": {"content": "{}"}}],
                "usage": {"total_tokens": 3},
            },
        )

    monkeypatch.setattr("httpx.post", fake_post)
    provider = OpenAICompatibleChatProvider("https://example.test/v1", "qwen35-4b", "runtime", 3, 1)
    result = provider.complete([{"role": "user", "content": "test"}], json_mode=True)
    assert result.model == "qwen35-4b"
    assert calls[0][1]["chat_template_kwargs"] == {"enable_thinking": False}
    assert calls[0][1]["response_format"] == {"type": "json_object"}

    attempts = []

    def timeout_post(*args, **kwargs):
        attempts.append(1)
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr("httpx.post", timeout_post)
    monkeypatch.setattr("time.sleep", lambda _: None)
    failing = OpenAICompatibleChatProvider("https://example.test/v1", "qwen35-4b", "runtime", 3, 1)
    try:
        failing.complete([{"role": "user", "content": "test"}])
    except ProviderRequestError:
        assert len(attempts) == 2
    else:
        raise AssertionError("provider retry exhaustion must be visible")


def test_builtin_golden_cases_run_without_changing_production():
    class FixedGoldenProvider:
        name = "mock"
        model = "mock"

        def complete(self, messages, **kwargs):
            content = messages[0]["content"]
            salience = "episodic" if "刚才临时" in content else "durable"
            return ChatResult(
                content=(
                    '{"candidates":[{"subject":"V100","predicate":"power_limit",'
                    f'"value":"150W","memory_text":"V100 {salience}","salience":"{salience}",'
                    f'"durable":{str(salience == "durable").lower()},"confidence":0.9}}]}}'
                ),
                model="mock",
            )

    with SessionLocal() as db:
        from sqlalchemy import select

        from app.models import PromptDefinition, PromptVersion

        definition = db.scalar(
            select(PromptDefinition).where(PromptDefinition.name == "memory_extract")
        )
        version = db.scalar(
            select(PromptVersion).where(
                PromptVersion.prompt_definition_id == definition.id,
                PromptVersion.status == "production",
            )
        )
        results = run_prompt_tests(db, version, FixedGoldenProvider())
        assert results and all(item["passed"] for item in results)
        db.refresh(version)
        assert version.status == "production"
