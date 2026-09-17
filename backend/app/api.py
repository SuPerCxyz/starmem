from __future__ import annotations

import difflib
import json
import time
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from app.ask import ask as ask_service
from app.config import get_settings
from app.db import get_db
from app.memory_engine import (
    apply_candidate,
    confirm_memory,
    create_candidate,
    delete_memory,
    expire_memory,
)
from app.metrics import observe
from app.models import (
    AIJob,
    ApiToken,
    Attachment,
    Entity,
    Entry,
    EntryEntity,
    EntryTag,
    EntryVersion,
    IngestionJob,
    Knowledge,
    Memory,
    PromptDefinition,
    PromptTestCase,
    PromptVersion,
    SavedSearch,
    Tag,
    User,
    UserSession,
    UserSetting,
)
from app.prompting import (
    PromptValidationError,
    clone_builtin_draft,
    create_draft,
    promote_version,
    resolve_prompt,
    restore_builtin,
    run_prompt_tests,
    version_diff,
)
from app.providers import get_chat_provider
from app.schemas import (
    AIJobOut,
    ApiTokenCreate,
    ApiTokenOut,
    AskOut,
    AskRequest,
    AttachmentOut,
    BatchReprocessInput,
    BatchReprocessOut,
    EntityInput,
    EntityOut,
    EntryAIStatusOut,
    EntryCreate,
    EntryListOut,
    EntryMetadataInput,
    EntryMetadataOut,
    EntryOut,
    EntryUpdate,
    EntryVersionOut,
    ImportOut,
    IngestionCorrection,
    IngestionOut,
    KnowledgeOut,
    KnowledgeSummaryInput,
    LoginInput,
    LoginOut,
    MaintenanceOut,
    MemoryApplyOut,
    MemoryCandidateCreate,
    MemoryOut,
    MergeInput,
    PromptDraftInput,
    PromptOut,
    PromptPreviewOut,
    PromptTestCaseInput,
    PromptTestCaseOut,
    PromptTestOut,
    PromptVersionOut,
    RelatedEntryOut,
    RelationOut,
    RenameInput,
    ReviewOut,
    SafetyFindingOut,
    SafetyScanOut,
    SavedSearchInput,
    SavedSearchOut,
    SavedSearchUpdate,
    SearchOut,
    SettingsOut,
    SettingsUpdate,
    SimilarEntryOut,
    SmartViewOut,
    TagInput,
    TagOut,
    UrlIngestInput,
    UserOut,
    WorkbenchSummaryOut,
)
from app.security import (
    create_session,
    get_current_user,
    hash_secret,
    new_secret,
    require_csrf,
    verify_password,
)
from app.services.analytics import record_query
from app.services.batch import rebuild_embeddings, reprocess_batch
from app.services.curation import (
    entry_ai_status,
    entry_ai_status_items,
    entry_metadata,
    entry_signal_map,
    merge_entity,
    merge_object,
    rename_object,
    set_object_status,
    update_entry_metadata,
)
from app.services.entries import create_entry as create_entry_service
from app.services.entries import (
    get_entry,
    list_entries,
    reprocess_entry,
    soft_delete_entry,
    update_entry,
)
from app.services.import_parsers import ImportParseError
from app.services.ingestion import (
    correct_job as correct_ingestion_job,
)
from app.services.ingestion import (
    get_job as get_ingestion_job,
)
from app.services.ingestion import (
    list_jobs as list_ingestion_jobs,
)
from app.services.ingestion import (
    retry_job as retry_ingestion_job,
)
from app.services.ingestion import (
    submit_file,
    submit_url,
)
from app.services.portability import build_export, import_native_records
from app.services.related import related_entries
from app.services.relations import list_relations
from app.services.safety import get_entry_scan, scan_entry
from app.services.search import search as search_service
from app.services.workbench import (
    generate_knowledge_summary,
    list_knowledge,
    list_workbench,
    run_smart_view,
    saved_search_input,
    saved_search_results,
    similar_entries,
    smart_view_definitions,
    validate_saved_filters,
    validate_source_scope,
    workbench_summary,
)
from app.services.workbench import (
    review as workbench_review,
)
from app.storage import StorageError, read_attachment, verify_attachment
from app.worker import process_entry

router = APIRouter(prefix="/api/v1")
settings = get_settings()
DbSession = Annotated[Session, Depends(get_db)]
ReadUser = Annotated[User, Depends(get_current_user)]
WriteUser = Annotated[User, Depends(require_csrf)]


def _entry_or_404(db: Session, entry_id: UUID):
    entry = get_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry


def _entries_out(db: Session, entries: list[Entry]) -> list[EntryOut]:
    signals = entry_signal_map(db, [entry.id for entry in entries])
    payloads: list[EntryOut] = []
    for entry in entries:
        data = signals.get(entry.id, {})
        out = EntryOut.model_validate(entry)
        out.tags = list(data.get("tags", []))
        out.ai_status_items = entry_ai_status_items(data.get("jobs", {}))
        payloads.append(out)
    return payloads


def _attachment_out(attachment: Attachment) -> AttachmentOut:
    return AttachmentOut(
        id=attachment.id,
        entry_id=attachment.entry_id,
        original_filename=attachment.original_filename,
        media_type=attachment.media_type,
        size_bytes=attachment.size_bytes,
        content_hash=attachment.content_hash,
        processing_status=attachment.processing_status,
        metadata_json=attachment.metadata_json or {},
        download_url=f"/api/v1/attachments/{attachment.id}",
        created_at=attachment.created_at,
    )


def _ingestion_out(job: IngestionJob, attachments: list[Attachment]) -> IngestionOut:
    if job.entry_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Import Entry missing"
        )
    return IngestionOut(
        job_id=job.id,
        entry_id=job.entry_id,
        input_kind=job.input_kind,
        status=job.status,
        phase=job.phase,
        attempt=job.attempt,
        original_name=job.original_name,
        media_type=job.media_type,
        source_uri=job.source_uri,
        metadata_json=job.metadata_json or {},
        error_code=job.error_code,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        attachments=[_attachment_out(item) for item in attachments],
    )


@router.post("/auth/login", response_model=LoginOut)
def login(payload: LoginInput, response: Response, db: DbSession) -> LoginOut:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    token, session = create_session(db, user)
    max_age = 60 * 60 * 24 * 30
    response.set_cookie(
        "starmem_session",
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=max_age,
        path="/",
    )
    response.set_cookie(
        "starmem_csrf",
        session.csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=max_age,
        path="/",
    )
    return LoginOut(user=user, csrf_token=session.csrf_token)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: DbSession, _: WriteUser) -> None:
    raw_token = request.cookies.get("starmem_session")
    if raw_token:
        session = db.scalar(
            select(UserSession).where(UserSession.token_hash == hash_secret(raw_token))
        )
        if session:
            session.revoked_at = datetime.now(UTC)
            db.commit()
    response.delete_cookie("starmem_session", path="/")
    response.delete_cookie("starmem_csrf", path="/")


@router.get("/auth/me", response_model=UserOut)
def me(user: ReadUser) -> User:
    return user


@router.get("/settings", response_model=SettingsOut)
def read_settings(db: DbSession, user: ReadUser) -> UserSetting:
    settings_row = db.get(UserSetting, user.id)
    if not settings_row:
        settings_row = UserSetting(user_id=user.id)
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return settings_row


@router.patch("/settings", response_model=SettingsOut)
def update_settings(payload: SettingsUpdate, db: DbSession, user: WriteUser) -> UserSetting:
    if payload.default_source_scope not in {"all", "native", "external"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported source scope"
        )
    allowed_routes = {"classification", "summary", "memory", "chat", "embedding", "reranker"}
    if payload.model_routing is not None:
        unsupported = set(payload.model_routing) - allowed_routes
        if unsupported:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported model routing task: {sorted(unsupported)[0]}",
            )
    settings_row = db.get(UserSetting, user.id)
    if not settings_row:
        settings_row = UserSetting(user_id=user.id)
        db.add(settings_row)
    if "global_ai_instructions" in payload.model_fields_set:
        settings_row.global_ai_instructions = payload.global_ai_instructions
    if "default_source_scope" in payload.model_fields_set:
        settings_row.default_source_scope = payload.default_source_scope
    if "model_routing" in payload.model_fields_set:
        settings_row.model_routing = {
            task: route.model_dump() for task, route in (payload.model_routing or {}).items()
        }
    db.commit()
    db.refresh(settings_row)
    return settings_row


@router.post("/auth/tokens", response_model=ApiTokenOut, status_code=status.HTTP_201_CREATED)
def create_api_token(payload: ApiTokenCreate, db: DbSession, user: WriteUser) -> ApiTokenOut:
    name = " ".join(payload.name.strip().split())
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Token name cannot be blank"
        )
    raw_token = new_secret()
    token = ApiToken(
        user_id=user.id,
        name=name,
        token_hash=hash_secret(raw_token),
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return ApiTokenOut(
        id=token.id,
        name=token.name,
        created_at=token.created_at,
        last_used_at=token.last_used_at,
        token=raw_token,
    )


@router.get("/auth/tokens", response_model=list[ApiTokenOut])
def list_api_tokens(db: DbSession, user: ReadUser) -> list[ApiToken]:
    return db.scalars(
        select(ApiToken)
        .where(ApiToken.user_id == user.id, ApiToken.revoked_at.is_(None))
        .order_by(ApiToken.created_at.desc())
    ).all()


@router.delete("/auth/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_token(token_id: UUID, db: DbSession, user: WriteUser) -> None:
    token = db.scalar(
        select(ApiToken).where(
            ApiToken.id == token_id,
            ApiToken.user_id == user.id,
            ApiToken.revoked_at.is_(None),
        )
    )
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API token not found")
    token.revoked_at = datetime.now(UTC)
    db.commit()


def _prompt_version_or_404(db: Session, name: str, version_number: int) -> PromptVersion:
    version = db.scalar(
        select(PromptVersion)
        .join(PromptDefinition, PromptDefinition.id == PromptVersion.prompt_definition_id)
        .where(
            PromptDefinition.name == name,
            PromptVersion.version_number == version_number,
        )
    )
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt version not found"
        )
    return version


@router.get("/prompts", response_model=list[PromptOut])
def list_prompts(db: DbSession, _: ReadUser) -> list[PromptOut]:
    definitions = db.scalars(select(PromptDefinition).order_by(PromptDefinition.name)).all()
    return [
        PromptOut(
            name=definition.name,
            description=definition.description,
            versions=[
                PromptVersionOut.model_validate(version)
                for version in db.scalars(
                    select(PromptVersion)
                    .where(PromptVersion.prompt_definition_id == definition.id)
                    .order_by(PromptVersion.version_number.desc())
                ).all()
            ],
        )
        for definition in definitions
    ]


@router.get("/prompts/{name}", response_model=PromptOut)
def read_prompt(name: str, db: DbSession, _: ReadUser) -> PromptOut:
    definition = db.scalar(select(PromptDefinition).where(PromptDefinition.name == name))
    if not definition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    versions = db.scalars(
        select(PromptVersion)
        .where(PromptVersion.prompt_definition_id == definition.id)
        .order_by(PromptVersion.version_number.desc())
    ).all()
    return PromptOut(
        name=name,
        description=definition.description,
        versions=[PromptVersionOut.model_validate(version) for version in versions],
    )


@router.post("/prompts/{name}/draft", response_model=PromptVersionOut, status_code=201)
def draft_prompt(
    name: str, payload: PromptDraftInput, db: DbSession, user: WriteUser
) -> PromptVersion:
    try:
        version = create_draft(
            db,
            name,
            user_instructions=payload.user_instructions,
            prompt_text=payload.prompt_text,
            provider=payload.provider,
            model=payload.model,
            temperature=payload.temperature,
            top_p=payload.top_p,
            max_tokens=payload.max_tokens,
            created_by="user",
        )
    except PromptValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    db.commit()
    db.refresh(version)
    return version


@router.post("/prompts/{name}/clone", response_model=PromptVersionOut, status_code=201)
def clone_prompt(name: str, db: DbSession, _: WriteUser) -> PromptVersion:
    try:
        version = clone_builtin_draft(db, name, created_by="user")
    except PromptValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    db.commit()
    db.refresh(version)
    return version


@router.get("/prompts/{name}/preview", response_model=PromptPreviewOut)
def preview_prompt(name: str, db: DbSession, _: ReadUser) -> PromptPreviewOut:
    try:
        resolved = resolve_prompt(db, name)
    except PromptValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PromptPreviewOut(
        name=resolved.name,
        version=resolved.version,
        schema_version=resolved.schema_version,
        prompt_hash=resolved.prompt_hash,
        content=resolved.content,
    )


@router.get("/prompts/{name}/versions/{version_number}/diff")
def prompt_diff(
    name: str,
    version_number: int,
    db: DbSession,
    _: ReadUser,
    against: int | None = None,
) -> dict[str, str]:
    target = _prompt_version_or_404(db, name, version_number)
    if against is None:
        previous = db.scalar(
            select(PromptVersion)
            .where(
                PromptVersion.prompt_definition_id == target.prompt_definition_id,
                PromptVersion.version_number < version_number,
            )
            .order_by(PromptVersion.version_number.desc())
        )
    else:
        previous = _prompt_version_or_404(db, name, against)
    return {"diff": version_diff(previous, target) if previous else target.prompt_text}


@router.post("/prompts/{name}/versions/{version_number}/promote", response_model=PromptVersionOut)
def promote_prompt(name: str, version_number: int, db: DbSession, user: WriteUser) -> PromptVersion:
    version = _prompt_version_or_404(db, name, version_number)
    version.created_by = version.created_by or str(user.id)
    promote_version(db, version)
    db.commit()
    db.refresh(version)
    return version


@router.post("/prompts/{name}/restore-default", response_model=PromptVersionOut)
def restore_default_prompt(name: str, db: DbSession, _: WriteUser) -> PromptVersion:
    try:
        version = restore_builtin(db, name)
    except PromptValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    db.commit()
    db.refresh(version)
    return version


@router.post("/prompts/{name}/versions/{version_number}/test", response_model=PromptTestOut)
def test_prompt(name: str, version_number: int, db: DbSession, _: ReadUser) -> PromptTestOut:
    version = _prompt_version_or_404(db, name, version_number)
    try:
        results = run_prompt_tests(db, version, get_chat_provider())
    except PromptValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return PromptTestOut(version=version.version_number, results=results)


def _prompt_definition_or_404(db: Session, name: str) -> PromptDefinition:
    definition = db.scalar(select(PromptDefinition).where(PromptDefinition.name == name))
    if not definition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    return definition


@router.get("/prompts/{name}/test-cases", response_model=list[PromptTestCaseOut])
def list_prompt_test_cases(name: str, db: DbSession, _: ReadUser) -> list[PromptTestCase]:
    definition = _prompt_definition_or_404(db, name)
    return db.scalars(
        select(PromptTestCase)
        .where(PromptTestCase.prompt_definition_id == definition.id)
        .order_by(PromptTestCase.is_builtin.desc(), PromptTestCase.created_at)
    ).all()


@router.post("/prompts/{name}/test-cases", response_model=PromptTestCaseOut, status_code=201)
def create_prompt_test_case(
    name: str, payload: PromptTestCaseInput, db: DbSession, _: WriteUser
) -> PromptTestCase:
    definition = _prompt_definition_or_404(db, name)
    case = PromptTestCase(
        prompt_definition_id=definition.id,
        name=payload.name.strip(),
        input_json=payload.input_json,
        expected_json=payload.expected_json,
        is_builtin=False,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.patch("/prompts/{name}/test-cases/{case_id}", response_model=PromptTestCaseOut)
def update_prompt_test_case(
    name: str, case_id: UUID, payload: PromptTestCaseInput, db: DbSession, _: WriteUser
) -> PromptTestCase:
    definition = _prompt_definition_or_404(db, name)
    case = db.scalar(
        select(PromptTestCase).where(
            PromptTestCase.id == case_id,
            PromptTestCase.prompt_definition_id == definition.id,
        )
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
    if case.is_builtin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Builtin test case cannot be edited"
        )
    case.name = payload.name.strip()
    case.input_json = payload.input_json
    case.expected_json = payload.expected_json
    db.commit()
    db.refresh(case)
    return case


@router.delete("/prompts/{name}/test-cases/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt_test_case(name: str, case_id: UUID, db: DbSession, _: WriteUser) -> None:
    definition = _prompt_definition_or_404(db, name)
    case = db.scalar(
        select(PromptTestCase).where(
            PromptTestCase.id == case_id,
            PromptTestCase.prompt_definition_id == definition.id,
        )
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
    if case.is_builtin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Builtin test case cannot be deleted"
        )
    db.delete(case)
    db.commit()


@router.get("/memories", response_model=list[MemoryOut])
def list_memories(
    db: DbSession,
    _: ReadUser,
    memory_status: str = Query(default="active", alias="status"),
    scope: str | None = None,
) -> list[Memory]:
    if memory_status not in {"active", "superseded", "conflicted", "expired", "deleted", "all"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported memory status"
        )
    statement = select(Memory).order_by(Memory.updated_at.desc(), Memory.created_at.desc())
    if memory_status != "all":
        statement = statement.where(Memory.status == memory_status)
    if scope:
        statement = statement.where(Memory.scope_key == scope)
    return db.scalars(statement.limit(100)).all()


@router.get("/memories/{memory_id}", response_model=MemoryOut)
def read_memory(memory_id: UUID, db: DbSession, _: ReadUser) -> Memory:
    memory = db.get(Memory, memory_id)
    if not memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    return memory


@router.post("/memories/{memory_id}/confirm", response_model=MemoryOut)
def confirm_memory_route(memory_id: UUID, db: DbSession, _: WriteUser) -> Memory:
    try:
        return confirm_memory(db, memory_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/memories/{memory_id}/expire", response_model=MemoryOut)
def expire_memory_route(memory_id: UUID, db: DbSession, _: WriteUser) -> Memory:
    memory = db.get(Memory, memory_id)
    if not memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    try:
        return expire_memory(db, memory)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory_route(memory_id: UUID, db: DbSession, _: WriteUser) -> None:
    memory = db.get(Memory, memory_id)
    if not memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    delete_memory(db, memory)


@router.post("/ask", response_model=AskOut)
def ask_route(payload: AskRequest, db: DbSession, _: ReadUser) -> AskOut:
    if payload.source_scope not in {"all", "native", "external"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported source scope"
        )
    started = time.perf_counter()
    result = ask_service(db, payload)
    record_query(
        db,
        query=payload.query,
        source_scope=payload.source_scope,
        result_count=len(result.sources),
        latency_ms=round((time.perf_counter() - started) * 1000),
    )
    return result


@router.get("/ai-jobs", response_model=list[AIJobOut])
def list_ai_jobs(
    db: DbSession,
    _: ReadUser,
    entry_id: UUID | None = None,
    job_status: str | None = Query(default=None, alias="status"),
) -> list[AIJob]:
    statement = select(AIJob).order_by(AIJob.created_at.desc()).limit(200)
    if entry_id:
        statement = statement.where(AIJob.entry_id == entry_id)
    if job_status:
        statement = statement.where(AIJob.status == job_status)
    return db.scalars(statement).all()


@router.get("/ai-jobs/{job_id}", response_model=AIJobOut)
def read_ai_job(job_id: UUID, db: DbSession, _: ReadUser) -> AIJob:
    job = db.get(AIJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI job not found")
    return job


@router.post("/ai-jobs/{job_id}/retry", response_model=AIJobOut)
def retry_ai_job(job_id: UUID, db: DbSession, _: WriteUser) -> AIJob:
    job = db.get(AIJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI job not found")
    job.status = "pending"
    job.error = None
    db.commit()
    try:
        process_entry.send(str(job.entry_id))
    except Exception:
        job.status = "retrying"
        job.error = "Queue unavailable; retry later."
        db.commit()
    db.refresh(job)
    return job


@router.post("/ingest/url", response_model=IngestionOut, status_code=status.HTTP_202_ACCEPTED)
def ingest_url(
    payload: UrlIngestInput,
    db: DbSession,
    _: WriteUser,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> IngestionOut:
    try:
        result = submit_url(
            db,
            url=payload.url,
            title=payload.title,
            idempotency_key=idempotency_key,
        )
    except ImportParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return _ingestion_out(result.job, result.attachments)


@router.post("/ingest/file", response_model=IngestionOut, status_code=status.HTTP_202_ACCEPTED)
async def ingest_file(
    db: DbSession,
    _: WriteUser,
    file: Annotated[UploadFile, File(...)],
    title: Annotated[str | None, Form(max_length=10_000)] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> IngestionOut:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Filename is required"
        )
    data = await file.read(get_settings().max_upload_bytes + 1)
    if len(data) > get_settings().max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Upload exceeds the configured size limit",
        )
    try:
        result = submit_file(
            db,
            data=data,
            filename=file.filename,
            media_type=file.content_type,
            title=title,
            idempotency_key=idempotency_key,
        )
    except ImportParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return _ingestion_out(result.job, result.attachments)


@router.get("/inbox", response_model=list[IngestionOut])
def inbox(
    db: DbSession,
    _: ReadUser,
    job_status: str | None = Query(default=None, alias="status"),
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[IngestionOut]:
    if job_status and job_status not in {"new", "processing", "processed", "failed"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported import status"
        )
    return [
        _ingestion_out(item.job, item.attachments)
        for item in list_ingestion_jobs(db, status=job_status, limit=limit)
    ]


@router.get("/inbox/{job_id}", response_model=IngestionOut)
def read_inbox_item(job_id: UUID, db: DbSession, _: ReadUser) -> IngestionOut:
    result = get_ingestion_job(db, job_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return _ingestion_out(result.job, result.attachments)


@router.post("/inbox/{job_id}/retry", response_model=IngestionOut)
def retry_inbox_item(job_id: UUID, db: DbSession, _: WriteUser) -> IngestionOut:
    try:
        result = retry_ingestion_job(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return _ingestion_out(result.job, result.attachments)


@router.patch("/inbox/{job_id}", response_model=IngestionOut)
def correct_inbox_item(
    job_id: UUID, payload: IngestionCorrection, db: DbSession, _: WriteUser
) -> IngestionOut:
    try:
        result = correct_ingestion_job(
            db,
            job_id=job_id,
            title=payload.title,
            content_type=payload.content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return _ingestion_out(result.job, result.attachments)


@router.get("/entries/{entry_id}/attachments", response_model=list[AttachmentOut])
def entry_attachments(entry_id: UUID, db: DbSession, _: ReadUser) -> list[AttachmentOut]:
    _entry_or_404(db, entry_id)
    attachments = db.scalars(
        select(Attachment).where(Attachment.entry_id == entry_id).order_by(Attachment.created_at)
    ).all()
    return [_attachment_out(item) for item in attachments]


@router.get("/attachments/{attachment_id}")
def download_attachment(attachment_id: UUID, db: DbSession, _: ReadUser) -> FileResponse:
    attachment = db.get(Attachment, attachment_id)
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    _entry_or_404(db, attachment.entry_id)
    try:
        path = read_attachment(attachment.storage_key)
        if not verify_attachment(attachment.storage_key, attachment.content_hash):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Attachment integrity check failed"
            )
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    filename = attachment.original_filename.replace("\r", "").replace("\n", "")[:255]
    return FileResponse(path, media_type=attachment.media_type, filename=filename or "attachment")


@router.post("/entries", response_model=EntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(payload: EntryCreate, db: DbSession, _: WriteUser):
    return create_entry_service(db, payload)


@router.get("/entries", response_model=EntryListOut)
def list_entry_items(
    db: DbSession,
    _: ReadUser,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    start: datetime | None = None,
    end: datetime | None = None,
    pinned: bool | None = None,
    favorite: bool | None = None,
) -> EntryListOut:
    items, next_cursor = list_entries(
        db, cursor=cursor, limit=limit, start=start, end=end, pinned=pinned, favorite=favorite
    )
    return EntryListOut(items=_entries_out(db, items), next_cursor=next_cursor)


@router.get("/entries/{entry_id}", response_model=EntryOut)
def read_entry(entry_id: UUID, db: DbSession, _: ReadUser) -> EntryOut:
    return _entries_out(db, [_entry_or_404(db, entry_id)])[0]


@router.get("/entries/{entry_id}/tags", response_model=list[TagOut])
def entry_tags(entry_id: UUID, db: DbSession, _: ReadUser) -> list[TagOut]:
    _entry_or_404(db, entry_id)
    rows = db.execute(
        select(Tag, EntryTag)
        .join(EntryTag, EntryTag.tag_id == Tag.id)
        .where(EntryTag.entry_id == entry_id, EntryTag.user_removed.is_(False))
        .order_by(Tag.name)
    ).all()
    return [
        TagOut(
            id=tag.id,
            name=tag.name,
            normalized_name=tag.normalized_name,
            source=link.source,
            user_confirmed=link.user_confirmed,
            user_removed=link.user_removed,
        )
        for tag, link in rows
    ]


@router.post("/entries/{entry_id}/tags", response_model=TagOut, status_code=201)
def add_entry_tag(entry_id: UUID, payload: TagInput, db: DbSession, _: WriteUser) -> TagOut:
    _entry_or_404(db, entry_id)
    name = " ".join(payload.name.strip().split())
    normalized = name.casefold()
    tag = db.scalar(select(Tag).where(Tag.normalized_name == normalized))
    if not tag:
        tag = Tag(name=name, normalized_name=normalized, source="user")
        db.add(tag)
        db.flush()
    link = db.get(EntryTag, (entry_id, tag.id))
    if not link:
        link = EntryTag(
            entry_id=entry_id,
            tag_id=tag.id,
            source="user",
            confidence=1.0,
            user_confirmed=True,
        )
        db.add(link)
    else:
        link.source = "user"
        link.confidence = 1.0
        link.user_confirmed = True
        link.user_removed = False
    db.commit()
    return TagOut(
        id=tag.id,
        name=tag.name,
        normalized_name=tag.normalized_name,
        source=link.source,
        user_confirmed=link.user_confirmed,
        user_removed=link.user_removed,
    )


@router.delete("/entries/{entry_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_entry_tag(entry_id: UUID, tag_id: UUID, db: DbSession, _: WriteUser) -> None:
    _entry_or_404(db, entry_id)
    link = db.get(EntryTag, (entry_id, tag_id))
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry tag not found")
    link.source = "user"
    link.user_confirmed = True
    link.user_removed = True
    db.commit()


@router.get("/entries/{entry_id}/entities", response_model=list[EntityOut])
def entry_entities(entry_id: UUID, db: DbSession, _: ReadUser) -> list[EntityOut]:
    _entry_or_404(db, entry_id)
    rows = db.execute(
        select(Entity, EntryEntity)
        .join(EntryEntity, EntryEntity.entity_id == Entity.id)
        .where(EntryEntity.entry_id == entry_id)
        .order_by(Entity.entity_type, Entity.canonical_name)
    ).all()
    return [
        EntityOut(
            id=entity.id,
            canonical_name=entity.canonical_name,
            normalized_name=entity.normalized_name,
            entity_type=entity.entity_type,
            source=link.source,
        )
        for entity, link in rows
    ]


@router.post("/entries/{entry_id}/entities", response_model=EntityOut, status_code=201)
def add_entry_entity(
    entry_id: UUID, payload: EntityInput, db: DbSession, _: WriteUser
) -> EntityOut:
    _entry_or_404(db, entry_id)
    normalized = " ".join(payload.name.strip().casefold().split())
    entity = db.scalar(
        select(Entity).where(
            Entity.entity_type == payload.entity_type,
            Entity.normalized_name == normalized,
        )
    )
    if not entity:
        entity = Entity(
            entity_type=payload.entity_type,
            canonical_name=payload.name.strip(),
            normalized_name=normalized,
        )
        db.add(entity)
        db.flush()
    link = db.get(EntryEntity, (entry_id, entity.id))
    if not link:
        db.add(
            EntryEntity(
                entry_id=entry_id,
                entity_id=entity.id,
                mention_text=payload.mention_text or payload.name,
                confidence=1.0,
                source="user",
            )
        )
    else:
        link.mention_text = payload.mention_text or payload.name
        link.confidence = 1.0
        link.source = "user"
    db.commit()
    return EntityOut(
        id=entity.id,
        canonical_name=entity.canonical_name,
        normalized_name=entity.normalized_name,
        entity_type=entity.entity_type,
        source="user",
    )


@router.patch("/entries/{entry_id}", response_model=EntryOut)
def patch_entry(entry_id: UUID, payload: EntryUpdate, db: DbSession, _: WriteUser):
    if "raw_content" in payload.model_fields_set and payload.raw_content is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="raw_content cannot be null"
        )
    return update_entry(db, _entry_or_404(db, entry_id), payload)


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: UUID, db: DbSession, _: WriteUser) -> None:
    soft_delete_entry(db, _entry_or_404(db, entry_id), datetime.now(UTC))


@router.post("/entries/{entry_id}/undelete", response_model=EntryOut)
def undelete_entry(entry_id: UUID, db: DbSession, _: WriteUser) -> Entry:
    entry = get_entry(db, entry_id, include_deleted=True)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    entry.deleted_at = None
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/entries/{entry_id}/versions", response_model=list[EntryVersionOut])
def entry_versions(entry_id: UUID, db: DbSession, _: ReadUser):
    _entry_or_404(db, entry_id)
    return db.scalars(
        select(EntryVersion)
        .where(EntryVersion.entry_id == entry_id)
        .order_by(EntryVersion.version_number.desc())
    ).all()


@router.get("/entries/{entry_id}/versions/{version_number}/diff")
def entry_version_diff(
    entry_id: UUID, version_number: int, db: DbSession, _: ReadUser
) -> dict[str, str]:
    versions = db.scalars(
        select(EntryVersion)
        .where(EntryVersion.entry_id == entry_id)
        .order_by(EntryVersion.version_number)
    ).all()
    target = next((item for item in versions if item.version_number == version_number), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry version not found")
    previous = next(
        (item for item in reversed(versions) if item.version_number < version_number), None
    )
    diff = difflib.unified_diff(
        (previous.raw_content if previous else "").splitlines(),
        target.raw_content.splitlines(),
        fromfile=f"v{previous.version_number if previous else 0}",
        tofile=f"v{target.version_number}",
        lineterm="",
    )
    return {"diff": "\n".join(diff)}


@router.post("/entries/{entry_id}/restore/{version_number}", response_model=EntryOut)
def restore_entry(entry_id: UUID, version_number: int, db: DbSession, _: WriteUser):
    entry = _entry_or_404(db, entry_id)
    version = db.scalar(
        select(EntryVersion).where(
            EntryVersion.entry_id == entry_id, EntryVersion.version_number == version_number
        )
    )
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry version not found")
    return update_entry(
        db, entry, EntryUpdate(title=version.title, raw_content=version.raw_content), "restore"
    )


@router.post("/entries/{entry_id}/reprocess", response_model=EntryOut)
def reprocess(entry_id: UUID, db: DbSession, _: WriteUser):
    return reprocess_entry(db, _entry_or_404(db, entry_id))


@router.post("/entries/reprocess-batch", response_model=BatchReprocessOut)
def reprocess_entries_batch(
    payload: BatchReprocessInput, db: DbSession, _: WriteUser
) -> BatchReprocessOut:
    try:
        return reprocess_batch(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.post("/maintenance/rebuild-embeddings", response_model=MaintenanceOut)
def trigger_embedding_rebuild(_: WriteUser) -> MaintenanceOut:
    try:
        detail = rebuild_embeddings()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return MaintenanceOut(accepted=True, detail=detail)


@router.get("/entries/{entry_id}/relations", response_model=list[RelationOut])
def entry_relations(
    entry_id: UUID,
    db: DbSession,
    _: ReadUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[RelationOut]:
    _entry_or_404(db, entry_id)
    return list_relations(db, entry_id, limit=limit)


@router.get("/entries/{entry_id}/metadata", response_model=EntryMetadataOut)
def read_entry_metadata(entry_id: UUID, db: DbSession, _: ReadUser) -> EntryMetadataOut:
    return entry_metadata(db, _entry_or_404(db, entry_id))


@router.patch("/entries/{entry_id}/metadata", response_model=EntryMetadataOut)
def patch_entry_metadata(
    entry_id: UUID, payload: EntryMetadataInput, db: DbSession, _: WriteUser
) -> EntryMetadataOut:
    try:
        return update_entry_metadata(db, _entry_or_404(db, entry_id), payload)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.post(
    "/entries/{entry_id}/memory-candidates", response_model=MemoryApplyOut, status_code=201
)
def create_memory_candidate_route(
    entry_id: UUID, payload: MemoryCandidateCreate, db: DbSession, _: WriteUser
) -> MemoryApplyOut:
    entry = _entry_or_404(db, entry_id)
    try:
        candidate = create_candidate(
            db,
            entry_id=entry.id,
            subject=payload.subject,
            predicate=payload.predicate,
            value=payload.value,
            memory_text=payload.memory_text,
            salience=payload.salience,
            durable=payload.durable,
            confidence=payload.confidence,
            generation=entry.ai_generation,
        )
        decision, memory = apply_candidate(db, candidate)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return MemoryApplyOut(
        operation=decision.operation,
        memory=MemoryOut.model_validate(memory) if memory else None,
    )


@router.get("/search", response_model=SearchOut)
def search(
    q: Annotated[str, Query(min_length=1, max_length=500)],
    db: DbSession,
    _: ReadUser,
    mode: str = "hybrid",
    source_scope: str = "all",
    source_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    start: datetime | None = None,
    end: datetime | None = None,
    content_type: str | None = None,
    tag: str | None = None,
    entity: str | None = None,
    project: str | None = None,
    topic: str | None = None,
) -> SearchOut:
    started = time.perf_counter()
    if mode not in {"hybrid", "fulltext", "semantic"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported search mode"
        )
    if source_scope not in {"all", "native", "external"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported source scope"
        )
    outcome = search_service(
        db,
        q,
        mode=mode,
        limit=limit,
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
    observe("search", latency_ms=round((time.perf_counter() - started) * 1000))
    return SearchOut(
        items=outcome.items,
        semantic_available=outcome.semantic_available,
        mode=mode,
        filtered_low_relevance=outcome.filtered_low_relevance,
    )


def _safety_out(scan) -> SafetyScanOut:
    return SafetyScanOut(
        entry_id=scan.entry_id,
        detected=scan.detected,
        findings=[SafetyFindingOut.model_validate(item) for item in (scan.findings_json or [])],
        content_hash=scan.content_hash,
        scanner_version=scan.scanner_version,
        scanned_at=scan.scanned_at,
    )


@router.get("/entries/{entry_id}/safety", response_model=SafetyScanOut)
def entry_safety(entry_id: UUID, db: DbSession, _: ReadUser) -> SafetyScanOut:
    entry = _entry_or_404(db, entry_id)
    scan = get_entry_scan(db, entry.id)
    if not scan:
        scan = scan_entry(db, entry)
        db.commit()
        db.refresh(scan)
    return _safety_out(scan)


@router.post("/entries/{entry_id}/safety/rescan", response_model=SafetyScanOut)
def rescan_entry_safety(entry_id: UUID, db: DbSession, _: WriteUser) -> SafetyScanOut:
    entry = _entry_or_404(db, entry_id)
    scan = scan_entry(db, entry)
    db.commit()
    db.refresh(scan)
    return _safety_out(scan)


@router.get("/entries/{entry_id}/similar", response_model=list[SimilarEntryOut])
def entry_similar(
    entry_id: UUID,
    db: DbSession,
    _: ReadUser,
    source_scope: str = "all",
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> list[SimilarEntryOut]:
    try:
        return similar_entries(db, entry_id, source_scope=source_scope, limit=limit)
    except ValueError as exc:
        if str(exc) == "Unsupported source scope":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/entries/{entry_id}/related", response_model=list[RelatedEntryOut])
def entry_related(
    entry_id: UUID,
    db: DbSession,
    _: ReadUser,
    source_scope: str = "all",
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> list[RelatedEntryOut]:
    try:
        return related_entries(db, entry_id, source_scope=source_scope, limit=limit)
    except ValueError as exc:
        if str(exc) == "Unsupported source scope":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/entries/{entry_id}/ai-status", response_model=EntryAIStatusOut)
def entry_ai_status_route(entry_id: UUID, db: DbSession, _: ReadUser) -> EntryAIStatusOut:
    return entry_ai_status(db, _entry_or_404(db, entry_id))


@router.get("/export")
def export_native(
    db: DbSession,
    _: ReadUser,
    export_format: str = Query(default="json", alias="format"),
    source_scope: str = "all",
) -> Response:
    try:
        bundle = build_export(db, export_format=export_format, source_scope=source_scope)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return Response(
        content=bundle.content,
        media_type=bundle.media_type,
        headers={"Content-Disposition": f'attachment; filename="{bundle.filename}"'},
    )


@router.post("/import", response_model=ImportOut, status_code=status.HTTP_201_CREATED)
async def import_native(
    db: DbSession,
    _: WriteUser,
    file: Annotated[UploadFile, File(...)],
) -> ImportOut:
    filename = file.filename or ""
    if not filename.lower().endswith((".json", ".jsonl")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only StarMem JSON or JSONL imports are supported",
        )
    data = await file.read(get_settings().max_upload_bytes + 1)
    if len(data) > get_settings().max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Import exceeds the configured size limit",
        )
    try:
        result = import_native_records(db, data, filename=filename)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return ImportOut(
        created_count=result.created_count,
        skipped_count=result.skipped_count,
        entry_ids=[UUID(entry_id) for entry_id in result.entry_ids],
        errors=result.errors,
    )


def _workbench_list(kind: str, db: Session, source_scope: str, limit: int):
    try:
        return list_workbench(db, kind=kind, source_scope=source_scope, limit=limit)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


def _workbench_detail(kind: str, item_id: UUID, db: Session, source_scope: str):
    try:
        return workbench_summary(db, kind=kind, item_id=item_id, source_scope=source_scope)
    except ValueError as exc:
        code = (
            status.HTTP_422_UNPROCESSABLE_ENTITY
            if str(exc) == "Unsupported source scope"
            else status.HTTP_404_NOT_FOUND
        )
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.get("/projects", response_model=list[WorkbenchSummaryOut])
def list_projects(
    db: DbSession,
    _: ReadUser,
    source_scope: str = "all",
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[WorkbenchSummaryOut]:
    return _workbench_list("project", db, source_scope, limit)


@router.get("/projects/{project_id}", response_model=WorkbenchSummaryOut)
def read_project(
    project_id: UUID, db: DbSession, _: ReadUser, source_scope: str = "all"
) -> WorkbenchSummaryOut:
    return _workbench_detail("project", project_id, db, source_scope)


def _curation_result(action) -> dict[str, object]:
    try:
        return action()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/projects/{project_id}")
def rename_project(
    project_id: UUID, payload: RenameInput, db: DbSession, _: WriteUser
) -> dict[str, object]:
    return _curation_result(lambda: rename_object(db, "project", project_id, payload.name))


@router.post("/projects/{project_id}/merge")
def merge_project(
    project_id: UUID, payload: MergeInput, db: DbSession, _: WriteUser
) -> dict[str, object]:
    return _curation_result(lambda: merge_object(db, "project", project_id, payload.target_id))


@router.post("/projects/{project_id}/exclude")
def exclude_project(project_id: UUID, db: DbSession, _: WriteUser) -> dict[str, object]:
    return _curation_result(lambda: set_object_status(db, "project", project_id, "excluded"))


@router.post("/projects/{project_id}/restore")
def restore_project(project_id: UUID, db: DbSession, _: WriteUser) -> dict[str, object]:
    return _curation_result(lambda: set_object_status(db, "project", project_id, "active"))


@router.get("/topics", response_model=list[WorkbenchSummaryOut])
def list_topics(
    db: DbSession,
    _: ReadUser,
    source_scope: str = "all",
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[WorkbenchSummaryOut]:
    return _workbench_list("topic", db, source_scope, limit)


@router.get("/topics/{topic_id}", response_model=WorkbenchSummaryOut)
def read_topic(
    topic_id: UUID, db: DbSession, _: ReadUser, source_scope: str = "all"
) -> WorkbenchSummaryOut:
    return _workbench_detail("topic", topic_id, db, source_scope)


@router.patch("/topics/{topic_id}")
def rename_topic(
    topic_id: UUID, payload: RenameInput, db: DbSession, _: WriteUser
) -> dict[str, object]:
    return _curation_result(lambda: rename_object(db, "topic", topic_id, payload.name))


@router.post("/topics/{topic_id}/merge")
def merge_topic(
    topic_id: UUID, payload: MergeInput, db: DbSession, _: WriteUser
) -> dict[str, object]:
    return _curation_result(lambda: merge_object(db, "topic", topic_id, payload.target_id))


@router.post("/topics/{topic_id}/exclude")
def exclude_topic(topic_id: UUID, db: DbSession, _: WriteUser) -> dict[str, object]:
    return _curation_result(lambda: set_object_status(db, "topic", topic_id, "excluded"))


@router.post("/topics/{topic_id}/restore")
def restore_topic(topic_id: UUID, db: DbSession, _: WriteUser) -> dict[str, object]:
    return _curation_result(lambda: set_object_status(db, "topic", topic_id, "active"))


@router.get("/entities", response_model=list[WorkbenchSummaryOut])
def list_entities(
    db: DbSession,
    _: ReadUser,
    source_scope: str = "all",
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[WorkbenchSummaryOut]:
    return _workbench_list("entity", db, source_scope, limit)


@router.get("/entities/{entity_id}", response_model=WorkbenchSummaryOut)
def read_entity(
    entity_id: UUID, db: DbSession, _: ReadUser, source_scope: str = "all"
) -> WorkbenchSummaryOut:
    return _workbench_detail("entity", entity_id, db, source_scope)


@router.patch("/entities/{entity_id}")
def rename_entity(
    entity_id: UUID, payload: RenameInput, db: DbSession, _: WriteUser
) -> dict[str, object]:
    return _curation_result(lambda: rename_object(db, "entity", entity_id, payload.name))


@router.post("/entities/{entity_id}/merge")
def merge_entity_route(
    entity_id: UUID, payload: MergeInput, db: DbSession, _: WriteUser
) -> dict[str, object]:
    return _curation_result(lambda: merge_entity(db, entity_id, payload.target_id))


@router.post("/entities/{entity_id}/exclude")
def exclude_entity(entity_id: UUID, db: DbSession, _: WriteUser) -> dict[str, object]:
    return _curation_result(lambda: set_object_status(db, "entity", entity_id, "excluded"))


@router.post("/entities/{entity_id}/restore")
def restore_entity(entity_id: UUID, db: DbSession, _: WriteUser) -> dict[str, object]:
    return _curation_result(lambda: set_object_status(db, "entity", entity_id, "active"))


@router.get("/reviews", response_model=ReviewOut)
def review_entries(
    db: DbSession,
    _: ReadUser,
    period: str = "week",
    start: datetime | None = None,
    end: datetime | None = None,
    source_scope: str = "all",
) -> ReviewOut:
    try:
        return workbench_review(db, period=period, start=start, end=end, source_scope=source_scope)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.get("/knowledge", response_model=list[KnowledgeOut])
def list_knowledge_summaries(
    db: DbSession,
    _: ReadUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[Knowledge]:
    return list_knowledge(db, limit=limit)


@router.post("/knowledge/summaries", response_model=KnowledgeOut, status_code=201)
def create_knowledge_summary(
    payload: KnowledgeSummaryInput, db: DbSession, _: WriteUser
) -> Knowledge:
    try:
        return generate_knowledge_summary(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.get("/smart-views", response_model=list[SmartViewOut])
def list_smart_views(_: ReadUser) -> list[SmartViewOut]:
    return smart_view_definitions()


@router.get("/smart-views/{view_id}", response_model=SmartViewOut)
def read_smart_view(view_id: str, db: DbSession, _: ReadUser) -> SmartViewOut:
    try:
        return run_smart_view(db, view_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _saved_search_or_404(db: Session, search_id: UUID, user_id: UUID) -> SavedSearch:
    saved = db.scalar(
        select(SavedSearch).where(SavedSearch.id == search_id, SavedSearch.user_id == user_id)
    )
    if not saved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")
    return saved


@router.get("/saved-searches", response_model=list[SavedSearchOut])
def list_saved_searches(db: DbSession, user: ReadUser) -> list[SavedSearch]:
    return db.scalars(
        select(SavedSearch)
        .where(SavedSearch.user_id == user.id)
        .order_by(SavedSearch.updated_at.desc(), SavedSearch.name)
    ).all()


@router.post("/saved-searches", response_model=SavedSearchOut, status_code=201)
def create_saved_search(payload: SavedSearchInput, db: DbSession, user: WriteUser) -> SavedSearch:
    try:
        values = saved_search_input(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    if db.scalar(
        select(SavedSearch).where(
            SavedSearch.user_id == user.id, SavedSearch.name == values["name"]
        )
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Saved search exists")
    saved = SavedSearch(user_id=user.id, **values)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


@router.get("/saved-searches/{search_id}", response_model=SavedSearchOut)
def read_saved_search(search_id: UUID, db: DbSession, user: ReadUser) -> SavedSearch:
    return _saved_search_or_404(db, search_id, user.id)


@router.patch("/saved-searches/{search_id}", response_model=SavedSearchOut)
def update_saved_search(
    search_id: UUID,
    payload: SavedSearchUpdate,
    db: DbSession,
    user: WriteUser,
) -> SavedSearch:
    saved = _saved_search_or_404(db, search_id, user.id)
    values: dict[str, object] = {}
    if "name" in payload.model_fields_set:
        name = " ".join((payload.name or "").strip().split())
        if not name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Saved search name blank"
            )
        values["name"] = name
    if "query" in payload.model_fields_set:
        query = (payload.query or "").strip()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Saved search query blank"
            )
        values["query"] = query
    if "source_scope" in payload.model_fields_set:
        try:
            values["source_scope"] = validate_source_scope(payload.source_scope or "")
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
    if "filters_json" in payload.model_fields_set:
        try:
            values["filters_json"] = validate_saved_filters(payload.filters_json or {})
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
    if "name" in values:
        duplicate = db.scalar(
            select(SavedSearch).where(
                SavedSearch.user_id == user.id,
                SavedSearch.name == values["name"],
                SavedSearch.id != saved.id,
            )
        )
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Saved search exists")
    for field, value in values.items():
        setattr(saved, field, value)
    db.commit()
    db.refresh(saved)
    return saved


@router.delete("/saved-searches/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_search(search_id: UUID, db: DbSession, user: WriteUser) -> None:
    saved = _saved_search_or_404(db, search_id, user.id)
    db.delete(saved)
    db.commit()


@router.get("/saved-searches/{search_id}/results", response_model=SearchOut)
def saved_search_result_items(
    search_id: UUID,
    db: DbSession,
    user: ReadUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> SearchOut:
    saved = _saved_search_or_404(db, search_id, user.id)
    try:
        saved_filters = validate_saved_filters(saved.filters_json or {})
        outcome = saved_search_results(db, saved, limit=limit)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return SearchOut(
        items=outcome.items,
        semantic_available=outcome.semantic_available,
        mode=str(saved_filters.get("mode", "hybrid")),
    )
