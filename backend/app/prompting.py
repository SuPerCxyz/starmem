"""Prompt registry, layered resolution and strict output contracts."""

from __future__ import annotations

import difflib
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import PromptDefinition, PromptTestCase, PromptVersion, UserSetting
from app.providers import ChatProvider, ProviderUnavailable, task_messages

PROMPT_RESOURCE = Path(__file__).parent / "prompts" / "builtin.json"
SAFETY_CONTRACT = """You are a StarMem assistant.
- Use only the supplied evidence and runtime context.
- Never invent evidence, credentials, identifiers, or database operations.
- Return JSON that satisfies the requested output schema.
- Do not overwrite or silently supersede historical facts.
""".strip()


class ObservationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation_type: str = Field(min_length=1, max_length=64)
    data: dict[str, Any]
    confidence: float = Field(ge=0, le=1)


class ClassificationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_type: str = Field(min_length=1, max_length=64)
    content_types: list[str] = Field(default_factory=list, max_length=16)
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(default="", max_length=500)


class SummaryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=4_000)
    confidence: float = Field(ge=0, le=1)
    is_inference: bool = False


class TagsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tags: list[str] = Field(max_length=8)


class EntityItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    entity_type: str = Field(min_length=1, max_length=64)
    mention_text: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)


class EntitiesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entities: list[EntityItem] = Field(max_length=32)


class TemporalOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expressions: list[str] = Field(max_length=16)
    valid_from: str | None = None
    valid_to: str | None = None
    confidence: float = Field(ge=0, le=1)


class LabelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    confidence: float = Field(ge=0, le=1)


class RelationsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relations: list[dict[str, Any]] = Field(max_length=32)


class MemoryCandidateOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: str = Field(min_length=1, max_length=255)
    predicate: str = Field(min_length=1, max_length=255)
    value: str = Field(min_length=1, max_length=512)
    memory_text: str = Field(min_length=1, max_length=4_000)
    salience: Literal["durable", "episodic", "ignore"]
    durable: bool
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(default="", max_length=500)


class MemoryCandidatesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidates: list[MemoryCandidateOutput] = Field(max_length=16)


class SalienceOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    salience: Literal["durable", "episodic", "ignore"]
    durable: bool
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(default="", max_length=500)


class ReconcileOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: Literal["ADD", "SUPPORT", "SUPERSEDE", "CONFLICT", "MERGE", "IGNORE"]
    target_memory_id: str | None = None
    candidate: dict[str, Any] | None = None
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(default="", max_length=500)


class QueryUnderstandingOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: str = Field(min_length=1, max_length=64)
    keywords: list[str] = Field(max_length=32)
    identifiers: list[str] = Field(max_length=32)
    entities: list[str] = Field(max_length=32)
    time_hints: list[str] = Field(max_length=16)
    answer_mode: Literal["fact", "timeline", "summary", "search"]


class AnswerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1, max_length=8_000)
    confidence: float = Field(ge=0, le=1)
    is_inference: bool = False
    source_ids: list[str] = Field(max_length=32)


SCHEMAS: dict[str, type[BaseModel]] = {
    "observation_extract": ObservationOutput,
    "classification": ClassificationOutput,
    "summary": SummaryOutput,
    "tag": TagsOutput,
    "entity_extract": EntitiesOutput,
    "time_extract": TemporalOutput,
    "project_classify": LabelOutput,
    "topic_classify": LabelOutput,
    "relation_build": RelationsOutput,
    "memory_extract": MemoryCandidatesOutput,
    "salience_evaluate": SalienceOutput,
    "memory_reconcile": ReconcileOutput,
    "query_understanding": QueryUnderstandingOutput,
    "answer": AnswerOutput,
}


class PromptValidationError(ValueError):
    """The provider output is not valid for the selected Prompt contract."""


@dataclass(frozen=True)
class ResolvedPrompt:
    name: str
    version: int
    schema_version: str | None
    prompt_hash: str
    content: str
    provider: str | None
    model: str | None
    created_by: str


def _load_builtins() -> list[dict[str, Any]]:
    return json.loads(PROMPT_RESOURCE.read_text(encoding="utf-8"))


def _prompt_hash(prompt_text: str, user_instructions: str | None) -> str:
    raw = f"{SAFETY_CONTRACT}\n\n{prompt_text}\n\n{user_instructions or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def sync_builtin_prompts(db: Session) -> int:
    """Create missing system versions and builtin Golden Cases idempotently."""
    settings = get_settings()
    created = 0
    for builtin in _load_builtins():
        definition = db.scalar(
            select(PromptDefinition).where(PromptDefinition.name == builtin["name"])
        )
        if not definition:
            definition = PromptDefinition(
                name=builtin["name"], description=builtin.get("description")
            )
            db.add(definition)
            db.flush()
        production = db.scalar(
            select(PromptVersion).where(
                PromptVersion.prompt_definition_id == definition.id,
                PromptVersion.status == "production",
            )
        )
        if not production:
            db.add(
                PromptVersion(
                    prompt_definition_id=definition.id,
                    version_number=1,
                    status="production",
                    prompt_text=builtin["prompt_text"],
                    provider="openai-compatible",
                    model=settings.chat_model or None,
                    temperature=0.0,
                    top_p=1.0,
                    max_tokens=800,
                    input_schema_version=builtin.get("input_schema_version"),
                    output_schema_version=builtin.get("output_schema_version"),
                    prompt_hash=_prompt_hash(builtin["prompt_text"], None),
                    created_by="system",
                )
            )
            created += 1
        elif production.created_by == "system":
            production.provider = production.provider or "openai-compatible"
            production.model = production.model or settings.chat_model or None
            production.temperature = (
                production.temperature if production.temperature is not None else 0.0
            )
            production.top_p = production.top_p if production.top_p is not None else 1.0
            production.max_tokens = production.max_tokens or 800
        for case in builtin.get("golden_cases", []):
            exists = db.scalar(
                select(PromptTestCase).where(
                    PromptTestCase.prompt_definition_id == definition.id,
                    PromptTestCase.name == case["name"],
                    PromptTestCase.is_builtin.is_(True),
                )
            )
            if not exists:
                db.add(
                    PromptTestCase(
                        prompt_definition_id=definition.id,
                        name=case["name"],
                        input_json=case.get("input", {}),
                        expected_json=case.get("expected"),
                        assertions_json={"subset": True},
                        is_builtin=True,
                    )
                )
            else:
                exists.input_json = case.get("input", {})
                exists.expected_json = case.get("expected")
                exists.assertions_json = {"subset": True}
    return created


def resolve_prompt(
    db: Session, name: str, runtime_context: dict[str, Any] | None = None
) -> ResolvedPrompt:
    definition = db.scalar(select(PromptDefinition).where(PromptDefinition.name == name))
    if not definition:
        raise PromptValidationError(f"Prompt not registered: {name}")
    version = db.scalar(
        select(PromptVersion).where(
            PromptVersion.prompt_definition_id == definition.id,
            PromptVersion.status == "production",
        )
    )
    if not version:
        raise PromptValidationError(f"Prompt has no production version: {name}")
    context = json.dumps(runtime_context or {}, ensure_ascii=False, sort_keys=True)
    settings = db.scalar(select(UserSetting).order_by(UserSetting.updated_at.desc()))
    schema_text = json.dumps(SCHEMAS[name].model_json_schema(), ensure_ascii=False)
    content = (
        f"[System Safety Contract]\n{SAFETY_CONTRACT}\n\n"
        f"[Task Prompt]\n{version.prompt_text}\n\n"
        f"[Global User Instructions]\n"
        f"{settings.global_ai_instructions if settings else '(none)'}\n\n"
        f"[User Instructions]\n{version.user_instructions or '(none)'}\n\n"
        f"[Output Schema]\n{schema_text}\n\n"
        f"[Runtime Context]\n{context}"
    )
    return ResolvedPrompt(
        name=name,
        version=version.version_number,
        schema_version=version.output_schema_version,
        prompt_hash=_prompt_hash(version.prompt_text, version.user_instructions),
        content=content,
        provider=version.provider,
        model=version.model,
        created_by=version.created_by,
    )


def extract_json(content: str) -> Any:
    value = content.strip()
    if value.startswith("```"):
        value = value.strip("`").strip()
        if value.lower().startswith("json"):
            value = value[4:].strip()
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, character in enumerate(value):
            if character not in "[{":
                continue
            try:
                parsed, _ = decoder.raw_decode(value[index:])
                return parsed
            except json.JSONDecodeError:
                continue
    raise PromptValidationError("Provider output does not contain valid JSON")


def validate_output(prompt_name: str, content: str | dict[str, Any]) -> BaseModel:
    try:
        value = content if isinstance(content, dict) else extract_json(content)
        schema = SCHEMAS[prompt_name]
        return schema.model_validate(value)
    except (KeyError, ValidationError, PromptValidationError) as exc:
        raise PromptValidationError(f"Prompt Validation Failed: {prompt_name}") from exc


def _next_prompt_version(db: Session, definition: PromptDefinition) -> int:
    return (
        db.scalar(
            select(func.max(PromptVersion.version_number)).where(
                PromptVersion.prompt_definition_id == definition.id
            )
        )
        or 0
    ) + 1


def create_draft(
    db: Session,
    name: str,
    *,
    user_instructions: str | None,
    prompt_text: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
    created_by: str = "user",
) -> PromptVersion:
    definition = db.scalar(select(PromptDefinition).where(PromptDefinition.name == name))
    if not definition:
        raise PromptValidationError(f"Prompt not registered: {name}")
    base = db.scalar(
        select(PromptVersion)
        .where(PromptVersion.prompt_definition_id == definition.id)
        .order_by(PromptVersion.version_number.desc())
    )
    if not base:
        raise PromptValidationError(f"Prompt has no base version: {name}")
    task_prompt = (prompt_text or base.prompt_text).strip()
    if not task_prompt:
        raise PromptValidationError("Task Prompt cannot be blank")
    version = PromptVersion(
        prompt_definition_id=definition.id,
        version_number=_next_prompt_version(db, definition),
        status="draft",
        prompt_text=task_prompt,
        user_instructions=user_instructions,
        provider=provider or base.provider,
        model=model or base.model,
        temperature=base.temperature if temperature is None else temperature,
        top_p=base.top_p if top_p is None else top_p,
        max_tokens=base.max_tokens if max_tokens is None else max_tokens,
        input_schema_version=base.input_schema_version,
        output_schema_version=base.output_schema_version,
        prompt_hash=_prompt_hash(task_prompt, user_instructions),
        created_by=created_by,
    )
    db.add(version)
    db.flush()
    return version


def clone_builtin_draft(
    db: Session,
    name: str,
    *,
    user_instructions: str | None = None,
    created_by: str = "user",
) -> PromptVersion:
    """Clone the shipped builtin Prompt text into a fresh editable Draft."""
    builtin = next((item for item in _load_builtins() if item["name"] == name), None)
    if not builtin:
        raise PromptValidationError(f"Unknown builtin Prompt: {name}")
    definition = db.scalar(select(PromptDefinition).where(PromptDefinition.name == name))
    if not definition:
        raise PromptValidationError(f"Prompt not registered: {name}")
    settings = get_settings()
    version = PromptVersion(
        prompt_definition_id=definition.id,
        version_number=_next_prompt_version(db, definition),
        status="draft",
        prompt_text=builtin["prompt_text"],
        user_instructions=user_instructions,
        provider="openai-compatible",
        model=settings.chat_model or None,
        temperature=0.0,
        top_p=1.0,
        max_tokens=800,
        input_schema_version=builtin.get("input_schema_version"),
        output_schema_version=builtin.get("output_schema_version"),
        prompt_hash=_prompt_hash(builtin["prompt_text"], user_instructions),
        created_by=created_by,
    )
    db.add(version)
    db.flush()
    return version


def promote_version(db: Session, version: PromptVersion) -> PromptVersion:
    current = db.scalars(
        select(PromptVersion).where(
            PromptVersion.prompt_definition_id == version.prompt_definition_id,
            PromptVersion.status == "production",
        )
    ).all()
    for item in current:
        if item.id != version.id:
            item.status = "archived"
    version.status = "production"
    db.flush()
    return version


def restore_builtin(db: Session, name: str) -> PromptVersion:
    builtin = next((item for item in _load_builtins() if item["name"] == name), None)
    if not builtin:
        raise PromptValidationError(f"Unknown builtin Prompt: {name}")
    definition = db.scalar(select(PromptDefinition).where(PromptDefinition.name == name))
    if not definition:
        raise PromptValidationError(f"Prompt not registered: {name}")
    settings = get_settings()
    next_version = (
        db.scalar(
            select(func.max(PromptVersion.version_number)).where(
                PromptVersion.prompt_definition_id == definition.id
            )
        )
        or 0
    ) + 1
    version = PromptVersion(
        prompt_definition_id=definition.id,
        version_number=next_version,
        status="draft",
        prompt_text=builtin["prompt_text"],
        provider="openai-compatible",
        model=settings.chat_model or None,
        temperature=0.0,
        top_p=1.0,
        max_tokens=800,
        input_schema_version=builtin.get("input_schema_version"),
        output_schema_version=builtin.get("output_schema_version"),
        prompt_hash=_prompt_hash(builtin["prompt_text"], None),
        created_by="system",
    )
    db.add(version)
    db.flush()
    return promote_version(db, version)


def version_diff(first: PromptVersion, second: PromptVersion) -> str:
    first_text = f"{first.prompt_text}\n\n[User Instructions]\n{first.user_instructions or ''}"
    second_text = f"{second.prompt_text}\n\n[User Instructions]\n{second.user_instructions or ''}"
    return "\n".join(
        difflib.unified_diff(
            first_text.splitlines(),
            second_text.splitlines(),
            fromfile=f"v{first.version_number}",
            tofile=f"v{second.version_number}",
            lineterm="",
        )
    )


def _matches_expected(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and _matches_expected(actual[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return isinstance(actual, list) and all(
            any(_matches_expected(item, candidate) for item in actual) for candidate in expected
        )
    return actual == expected


def run_prompt_tests(
    db: Session, version: PromptVersion, provider: ChatProvider
) -> list[dict[str, Any]]:
    definition = db.get(PromptDefinition, version.prompt_definition_id)
    if not definition:
        raise PromptValidationError("Prompt definition not found")
    cases = db.scalars(
        select(PromptTestCase).where(PromptTestCase.prompt_definition_id == definition.id)
    ).all()
    results: list[dict[str, Any]] = []
    for case in cases:
        context = json.dumps(case.input_json, ensure_ascii=False)
        settings = db.scalar(select(UserSetting).order_by(UserSetting.updated_at.desc()))
        schema_text = json.dumps(SCHEMAS[definition.name].model_json_schema(), ensure_ascii=False)
        prompt = (
            f"[System Safety Contract]\n{SAFETY_CONTRACT}\n\n"
            f"[Task Prompt]\n{version.prompt_text}\n\n"
            f"[Global User Instructions]\n"
            f"{settings.global_ai_instructions if settings else '(none)'}\n\n"
            f"[User Instructions]\n{version.user_instructions or '(none)'}\n\n"
            f"[Output Schema]\n{schema_text}\n\n"
            f"[Runtime Context]\n{context}"
        )
        try:
            response = provider.complete(task_messages(prompt), json_mode=True)
            parsed = validate_output(definition.name, response.content).model_dump()
            expected = case.expected_json or {}
            passed = _matches_expected(parsed, expected)
            results.append({"name": case.name, "passed": passed, "output": parsed})
        except (PromptValidationError, ProviderUnavailable, RuntimeError) as exc:
            results.append({"name": case.name, "passed": False, "error": type(exc).__name__})
    return results
