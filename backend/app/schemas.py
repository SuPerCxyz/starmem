from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str


class LoginInput(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=512)


class LoginOut(BaseModel):
    user: UserOut
    csrf_token: str


class ApiTokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ApiTokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime
    last_used_at: datetime | None
    token: str | None = None


class PromptDraftInput(BaseModel):
    user_instructions: str | None = Field(default=None, max_length=8_000)
    prompt_text: str | None = Field(default=None, min_length=1, max_length=32_000)
    provider: str | None = Field(default=None, max_length=120)
    model: str | None = Field(default=None, max_length=255)
    temperature: float | None = Field(default=None, ge=0, le=2)
    top_p: float | None = Field(default=None, gt=0, le=1)
    max_tokens: int | None = Field(default=None, ge=1, le=32_000)


class PromptTestCaseInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    input_json: dict[str, object] = Field(default_factory=dict)
    expected_json: dict[str, object] | None = None


class PromptTestCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    input_json: dict[str, object]
    expected_json: dict[str, object] | None
    is_builtin: bool


class PromptVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    status: str
    prompt_text: str
    user_instructions: str | None
    provider: str | None
    model: str | None
    temperature: float | None
    top_p: float | None
    max_tokens: int | None
    input_schema_version: str | None
    output_schema_version: str | None
    prompt_hash: str
    created_at: datetime
    created_by: str


class PromptOut(BaseModel):
    name: str
    description: str | None
    versions: list[PromptVersionOut]


class PromptPreviewOut(BaseModel):
    name: str
    version: int
    schema_version: str | None
    prompt_hash: str
    content: str


class PromptTestOut(BaseModel):
    version: int
    results: list[dict[str, object]]


class MemoryCandidateCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=255)
    predicate: str = Field(min_length=1, max_length=255)
    value: str = Field(min_length=1, max_length=512)
    memory_text: str = Field(min_length=1, max_length=4_000)
    salience: str | None = Field(default=None, max_length=32)
    durable: bool | None = None
    confidence: float = Field(default=0.8, ge=0, le=1)


class MemoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_type: str
    subject_key: str
    predicate: str
    value_json: dict[str, object]
    memory_text: str
    status: str
    salience: str
    durable: bool
    confidence: float
    recorded_at: datetime | None
    observed_at: datetime | None
    valid_from: datetime | None
    valid_to: datetime | None
    superseded_at: datetime | None
    expired_at: datetime | None = None
    source_entry_id: UUID | None
    source_chunk_id: UUID | None


class MemoryApplyOut(BaseModel):
    operation: str
    memory: MemoryOut | None


class TagInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    normalized_name: str
    source: str
    user_confirmed: bool = False
    user_removed: bool = False


class EntityInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    entity_type: str = Field(min_length=1, max_length=64)
    mention_text: str | None = Field(default=None, max_length=500)


class EntityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    canonical_name: str
    normalized_name: str
    entity_type: str
    source: str = "user"


class RelationTargetOut(BaseModel):
    id: UUID
    title: str | None
    snippet: str
    created_at: datetime


class RelationOut(BaseModel):
    id: UUID
    relation_type: str
    direction: str
    source_type: str
    source_id: UUID
    target_type: str
    target_id: UUID
    confidence: float | None
    source: str
    created_at: datetime
    target: RelationTargetOut | None = None


class EntryMetadataInput(BaseModel):
    content_type: str | None = Field(default=None, max_length=64)
    content_types: list[str] | None = Field(default=None, max_length=16)
    summary: str | None = Field(default=None, max_length=4_000)
    project: str | None = Field(default=None, max_length=255)
    topic: str | None = Field(default=None, max_length=255)
    importance: int | None = Field(default=None, ge=0, le=100)


class EntryMetadataOut(BaseModel):
    entry_id: UUID
    content_type: str
    content_types: list[str] = Field(default_factory=list)
    content_types_locked: bool = False
    importance: int
    summary: str | None = None
    summary_locked: bool = False
    project: str | None = None
    project_locked: bool = False
    topic: str | None = None
    topic_locked: bool = False
    image_description: str | None = None
    image_description_status: str | None = None
    image_description_detail: str | None = None


class RenameInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class MergeInput(BaseModel):
    target_id: UUID


class BatchReprocessInput(BaseModel):
    entry_ids: list[UUID] | None = Field(default=None, max_length=200)
    source_scope: str = Field(default="all", max_length=32)
    start: datetime | None = None
    end: datetime | None = None
    content_type: str | None = Field(default=None, max_length=64)


class BatchReprocessOut(BaseModel):
    submitted_count: int
    failed_count: int
    entry_ids: list[UUID] = Field(default_factory=list)


class MaintenanceOut(BaseModel):
    accepted: bool
    detail: str


class EntryCreate(BaseModel):
    title: str | None = Field(default=None, max_length=10_000)
    raw_content: str = Field(min_length=1, max_length=2_000_000)
    content_format: str = Field(default="markdown", max_length=32)
    content_type: str = Field(default="note", max_length=64)
    content_types: list[str] = Field(default_factory=list, max_length=16)
    source_uri: str | None = Field(default=None, max_length=2_000)
    event_time_start: datetime | None = None
    event_time_end: datetime | None = None
    is_pinned: bool = False
    is_favorite: bool = False
    importance: int = Field(default=0, ge=0, le=100)


class EntryUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=10_000)
    raw_content: str | None = Field(default=None, min_length=1, max_length=2_000_000)
    content_format: str | None = Field(default=None, max_length=32)
    content_type: str | None = Field(default=None, max_length=64)
    content_types: list[str] | None = Field(default=None, max_length=16)
    event_time_start: datetime | None = None
    event_time_end: datetime | None = None
    is_pinned: bool | None = None
    is_favorite: bool | None = None
    importance: int | None = Field(default=None, ge=0, le=100)


class EntryAIStatusItemOut(BaseModel):
    job_id: UUID
    job_type: str
    label: str
    status: str
    error: str | None = None


class EntryAIStatusOut(BaseModel):
    entry_id: UUID
    ai_status: str
    generation: int
    items: list[EntryAIStatusItemOut] = Field(default_factory=list)


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    title: str | None
    raw_content: str
    content_format: str
    content_type: str
    content_types: list[str] = Field(default_factory=list)
    source_uri: str | None
    created_at: datetime
    updated_at: datetime
    event_time_start: datetime | None
    event_time_end: datetime | None
    deleted_at: datetime | None
    is_pinned: bool
    is_favorite: bool
    importance: int
    ai_status: str
    ai_generation: int
    tags: list[str] = Field(default_factory=list)
    ai_status_items: list[EntryAIStatusItemOut] = Field(default_factory=list)

    @model_validator(mode="after")
    def _fill_content_types(self) -> EntryOut:
        if not self.content_types and self.content_type:
            self.content_types = [self.content_type]
        return self


class EntryListOut(BaseModel):
    items: list[EntryOut]
    next_cursor: str | None = None


class UrlIngestInput(BaseModel):
    url: str = Field(min_length=8, max_length=2_000)
    title: str | None = Field(default=None, max_length=10_000)


class AttachmentOut(BaseModel):
    id: UUID
    entry_id: UUID
    original_filename: str
    media_type: str
    size_bytes: int
    content_hash: str
    processing_status: str
    metadata_json: dict[str, object]
    download_url: str
    created_at: datetime


class IngestionOut(BaseModel):
    job_id: UUID
    entry_id: UUID
    input_kind: str
    status: str
    phase: str | None
    attempt: int
    original_name: str | None
    media_type: str | None
    source_uri: str | None
    metadata_json: dict[str, object]
    error_code: str | None
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    attachments: list[AttachmentOut]


class ImportOut(BaseModel):
    created_count: int
    skipped_count: int
    entry_ids: list[UUID]
    errors: list[dict[str, object]]


class IngestionCorrection(BaseModel):
    title: str | None = Field(default=None, max_length=10_000)
    content_type: str | None = Field(default=None, max_length=64)


class EntryVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    raw_content: str
    title: str | None
    change_source: str
    created_at: datetime


class SearchResult(BaseModel):
    entry_id: UUID | None
    content_unit_id: UUID
    chunk_id: UUID | None = None
    attachment_id: UUID | None = None
    page_number: int | None = None
    provenance_type: str | None = None
    source_id: UUID
    source_name: str
    source_type: str
    source_uri: str | None = None
    final_url: str | None = None
    external_item_id: UUID | None = None
    external_id: str | None = None
    external_url: str | None = None
    external_created_at: datetime | None = None
    imported_at: datetime | None = None
    created_at: datetime | None
    snippet: str
    score: float
    match_reason: str
    exact_match: bool


class SearchOut(BaseModel):
    items: list[SearchResult]
    semantic_available: bool
    mode: str
    filtered_low_relevance: int = 0


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2_000)
    source_scope: str = Field(default="all", max_length=32)
    source_id: UUID | None = None
    limit: int = Field(default=8, ge=1, le=20)


class AskSource(BaseModel):
    entry_id: UUID | None
    content_unit_id: UUID
    chunk_id: UUID | None = None
    attachment_id: UUID | None = None
    page_number: int | None = None
    provenance_type: str | None = None
    source_id: UUID
    source_name: str
    source_type: str
    source_uri: str | None = None
    final_url: str | None = None
    external_item_id: UUID | None = None
    external_id: str | None = None
    external_url: str | None = None
    external_created_at: datetime | None = None
    imported_at: datetime | None = None
    created_at: datetime | None
    snippet: str
    score: float
    jump_target: str | None = None


class AskOut(BaseModel):
    answer: str
    confidence: float
    is_inference: bool
    sources: list[AskSource]
    semantic_available: bool
    query_understanding: dict[str, object]
    chat_available: bool
    filtered_low_relevance: int = 0


class AIJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entry_id: UUID
    job_type: str
    status: str
    provider: str | None
    model: str | None
    attempt: int
    generation: int
    error: str | None
    latency_ms: int | None
    token_usage: int | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    global_ai_instructions: str | None
    default_source_scope: str
    model_routing: dict[str, ModelRoute]


class SettingsUpdate(BaseModel):
    global_ai_instructions: str | None = Field(default=None, max_length=12_000)
    default_source_scope: str = Field(default="all", max_length=32)
    model_routing: dict[str, ModelRoute] | None = None


class ModelRoute(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1, max_length=120)
    model: str = Field(min_length=1, max_length=255)


class SafetyFindingOut(BaseModel):
    type: str
    line: int
    column: int


class SafetyScanOut(BaseModel):
    entry_id: UUID
    detected: bool
    findings: list[SafetyFindingOut]
    content_hash: str
    scanner_version: str
    scanned_at: datetime


class SimilarEntryOut(BaseModel):
    entry_id: UUID
    title: str | None
    score: float
    reason: str
    snippet: str
    created_at: datetime


class RelatedEntryOut(BaseModel):
    entry_id: UUID
    title: str | None
    score: float
    reasons: list[str] = Field(default_factory=list)
    snippet: str
    created_at: datetime


class SavedSearchInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    query: str = Field(min_length=1, max_length=500)
    source_scope: str = Field(default="all", max_length=32)
    filters_json: dict[str, object] = Field(default_factory=dict)


class SavedSearchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    query: str | None = Field(default=None, min_length=1, max_length=500)
    source_scope: str | None = Field(default=None, max_length=32)
    filters_json: dict[str, object] | None = None


class SavedSearchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    query: str
    source_scope: str
    filters_json: dict[str, object]
    created_at: datetime
    updated_at: datetime


class WorkbenchSummaryOut(BaseModel):
    id: UUID | None
    name: str
    kind: str
    status: str = "active"
    entity_type: str | None = None
    description: str | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    entry_count: int
    memory_count: int
    entry_ids: list[UUID] = Field(default_factory=list)
    memory_ids: list[UUID] = Field(default_factory=list)
    related: list[str] = Field(default_factory=list)


class WorkbenchItemOut(BaseModel):
    id: UUID
    kind: str
    title: str
    entry_id: UUID | None = None
    memory_id: UUID | None = None
    job_id: UUID | None = None
    status: str | None = None
    detail: str | None = None
    created_at: datetime | None = None
    score: float | None = None


class SmartViewOut(BaseModel):
    id: str
    name: str
    description: str
    items: list[WorkbenchItemOut]


class ReviewOut(BaseModel):
    start: datetime | None
    end: datetime | None
    counts: dict[str, int]
    items: list[WorkbenchItemOut]


class KnowledgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    content: str
    status: str
    metadata_json: dict[str, object]
    created_at: datetime
    updated_at: datetime


class KnowledgeSummaryInput(BaseModel):
    scope_type: str = Field(min_length=4, max_length=16)
    scope_value: str | None = Field(default=None, max_length=255)
    start: datetime | None = None
    end: datetime | None = None
    source_scope: str = Field(default="all", max_length=32)
