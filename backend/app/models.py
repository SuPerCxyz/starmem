from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def new_id() -> UUID:
    return uuid4()


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserSetting(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    global_ai_instructions: Mapped[str | None] = mapped_column(Text)
    default_source_scope: Mapped[str] = mapped_column(String(32), default="all")
    model_routing: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SavedSearch(Timestamped, Base):
    __tablename__ = "saved_searches"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_saved_search_user_name"),
        Index("ix_saved_search_user_updated", "user_id", "updated_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    query: Mapped[str] = mapped_column(Text)
    source_scope: Mapped[str] = mapped_column(String(32), default="all")
    filters_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    csrf_token: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Source(Timestamped, Base):
    __tablename__ = "sources"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    source_type: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_native: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class ExternalItem(Timestamped, Base):
    __tablename__ = "external_items"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_external_item_source_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="RESTRICT"), index=True
    )
    external_id: Mapped[str] = mapped_column(Text)
    external_parent_id: Mapped[str | None] = mapped_column(Text)
    item_type: Mapped[str] = mapped_column(String(64), default="document")
    title: Mapped[str | None] = mapped_column(Text)
    raw_content: Mapped[str | None] = mapped_column(Text)
    external_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[str | None] = mapped_column(String(128), index=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Attachment(Timestamped, Base):
    __tablename__ = "attachments"
    __table_args__ = (
        UniqueConstraint("entry_id", "content_hash", name="uq_attachment_entry_hash"),
        Index("ix_attachments_entry_created", "entry_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    entry_id: Mapped[UUID] = mapped_column(ForeignKey("entries.id", ondelete="CASCADE"), index=True)
    storage_key: Mapped[str] = mapped_column(String(255), unique=True)
    original_filename: Mapped[str] = mapped_column(Text)
    media_type: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    processing_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        UniqueConstraint("source_id", "job_type", "sync_cursor", name="uq_ingestion_cursor"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True
    )
    entry_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("entries.id", ondelete="CASCADE"), index=True
    )
    attachment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("attachments.id", ondelete="SET NULL"), index=True
    )
    job_type: Mapped[str] = mapped_column(String(64), default="sync")
    input_kind: Mapped[str] = mapped_column(String(32), default="external_sync", index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    phase: Mapped[str | None] = mapped_column(String(64))
    sync_cursor: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True)
    original_name: Mapped[str | None] = mapped_column(Text)
    media_type: Mapped[str | None] = mapped_column(String(255))
    source_uri: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Entry(Timestamped, Base):
    __tablename__ = "entries"
    __table_args__ = (
        Index(
            "ix_entries_visible_created", "created_at", postgresql_where=text("deleted_at IS NULL")
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str | None] = mapped_column(Text)
    raw_content: Mapped[str] = mapped_column(Text)
    content_format: Mapped[str] = mapped_column(String(32), default="markdown")
    content_type: Mapped[str] = mapped_column(String(64), default="note", index=True)
    content_types: Mapped[list[str]] = mapped_column(JSONB, default=list)
    source_uri: Mapped[str | None] = mapped_column(Text)
    event_time_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    event_time_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    importance: Mapped[int] = mapped_column(SmallInteger, default=0)
    ai_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    ai_generation: Mapped[int] = mapped_column(Integer, default=0)


class EntrySafetyScan(Timestamped, Base):
    __tablename__ = "entry_safety_scans"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("entries.id", ondelete="CASCADE"), unique=True, index=True
    )
    detected: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    findings_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    scanner_version: Mapped[str] = mapped_column(String(64), default="local-v1")
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EntryVersion(Base):
    __tablename__ = "entry_versions"
    __table_args__ = (
        UniqueConstraint("entry_id", "version_number", name="uq_entry_version_number"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    entry_id: Mapped[UUID] = mapped_column(ForeignKey("entries.id", ondelete="CASCADE"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    raw_content: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    change_source: Mapped[str] = mapped_column(String(32), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContentUnit(Timestamped, Base):
    __tablename__ = "content_units"
    __table_args__ = (
        Index("ix_content_units_source_owner", "source_id", "owner_type", "owner_id"),
        Index("ix_content_units_fts", "fts_vector", postgresql_using="gin"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    owner_type: Mapped[str] = mapped_column(String(32), index=True)
    owner_id: Mapped[UUID] = mapped_column(Uuid, index=True)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="RESTRICT"), index=True
    )
    entry_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("entries.id", ondelete="CASCADE"), index=True
    )
    external_item_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("external_items.id", ondelete="CASCADE"), index=True
    )
    attachment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("attachments.id", ondelete="SET NULL"), index=True
    )
    unit_type: Mapped[str] = mapped_column(String(64), default="entry")
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text)
    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    fts_vector: Mapped[str | None] = mapped_column(TSVECTOR)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(512))


class EntryChunk(Base):
    __tablename__ = "entry_chunks"
    __table_args__ = (UniqueConstraint("entry_id", "chunk_index", name="uq_entry_chunk_index"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    entry_id: Mapped[UUID] = mapped_column(ForeignKey("entries.id", ondelete="CASCADE"), index=True)
    content_unit_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_units.id", ondelete="SET NULL"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_type: Mapped[str] = mapped_column(String(32), default="prose")
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    start_offset: Mapped[int] = mapped_column(Integer, default=0)
    end_offset: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    normalized_name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(32), default="ai")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EntryTag(Base):
    __tablename__ = "entry_tags"

    entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("entries.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
    source: Mapped[str] = mapped_column(String(32), default="ai")
    confidence: Mapped[float | None] = mapped_column(Float)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_removed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Entity(Timestamped, Base):
    __tablename__ = "entities"
    __table_args__ = (
        UniqueConstraint("entity_type", "normalized_name", name="uq_entity_normalized"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    canonical_name: Mapped[str] = mapped_column(String(255))
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="active")


class EntryEntity(Base):
    __tablename__ = "entry_entities"

    entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("entries.id", ondelete="CASCADE"), primary_key=True
    )
    entity_id: Mapped[UUID] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True
    )
    mention_text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(32), default="ai")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Project(Timestamped, Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(32), default="ai")
    status: Mapped[str] = mapped_column(String(32), default="active")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Topic(Timestamped, Base):
    __tablename__ = "topics"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(32), default="ai")
    status: Mapped[str] = mapped_column(String(32), default="active")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    entry_id: Mapped[UUID] = mapped_column(ForeignKey("entries.id", ondelete="CASCADE"), index=True)
    content_unit_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_units.id", ondelete="SET NULL")
    )
    observation_type: Mapped[str] = mapped_column(String(64), index=True)
    data_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(32), default="ai")
    is_user_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    generation: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MemoryCandidate(Base):
    __tablename__ = "memory_candidates"
    __table_args__ = (
        Index("ix_memory_candidates_scope", "scope_key", "status"),
        Index("ix_memory_candidates_entry_generation", "entry_id", "generation"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    entry_id: Mapped[UUID] = mapped_column(ForeignKey("entries.id", ondelete="CASCADE"), index=True)
    observation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("observations.id", ondelete="SET NULL"), index=True
    )
    source_chunk_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("entry_chunks.id", ondelete="SET NULL"), index=True
    )
    subject_type: Mapped[str] = mapped_column(String(64), default="entity")
    subject_key: Mapped[str] = mapped_column(String(255), index=True)
    predicate: Mapped[str] = mapped_column(String(255), index=True)
    scope_key: Mapped[str] = mapped_column(String(512), index=True)
    value_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    value_key: Mapped[str] = mapped_column(String(512), index=True)
    memory_text: Mapped[str] = mapped_column(Text)
    salience: Mapped[str] = mapped_column(String(32), default="durable")
    durable: Mapped[bool] = mapped_column(Boolean, default=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    generation: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Memory(Timestamped, Base):
    __tablename__ = "memories"
    __table_args__ = (
        Index(
            "uq_memory_active_scope",
            "scope_key",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index("ix_memory_subject_predicate", "subject_key", "predicate"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    subject_type: Mapped[str] = mapped_column(String(64), default="entity")
    subject_key: Mapped[str] = mapped_column(String(255), index=True)
    predicate: Mapped[str] = mapped_column(String(255), index=True)
    scope_key: Mapped[str] = mapped_column(String(512), index=True)
    value_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    value_key: Mapped[str] = mapped_column(String(512), index=True)
    memory_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    salience: Mapped[str] = mapped_column(String(32), default="durable")
    durable: Mapped[bool] = mapped_column(Boolean, default=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("memories.id", ondelete="SET NULL")
    )
    source_entry_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("entries.id", ondelete="SET NULL")
    )
    source_chunk_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("entry_chunks.id", ondelete="SET NULL")
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(512))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class MemorySource(Base):
    __tablename__ = "memory_sources"
    __table_args__ = (
        UniqueConstraint("memory_id", "entry_id", "content_unit_id", name="uq_memory_source"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    memory_id: Mapped[UUID] = mapped_column(
        ForeignKey("memories.id", ondelete="CASCADE"), index=True
    )
    entry_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("entries.id", ondelete="CASCADE"), index=True
    )
    content_unit_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_units.id", ondelete="CASCADE"), index=True
    )
    support_type: Mapped[str] = mapped_column(String(32), default="primary")
    confidence: Mapped[float | None] = mapped_column(Float)


class Relation(Base):
    __tablename__ = "relations"
    __table_args__ = (
        UniqueConstraint(
            "source_type",
            "source_id",
            "relation_type",
            "target_type",
            "target_id",
            name="uq_relation",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    source_type: Mapped[str] = mapped_column(String(32))
    source_id: Mapped[UUID] = mapped_column(Uuid, index=True)
    relation_type: Mapped[str] = mapped_column(String(64), index=True)
    target_type: Mapped[str] = mapped_column(String(32))
    target_id: Mapped[UUID] = mapped_column(Uuid, index=True)
    confidence: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(32), default="ai")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Knowledge(Timestamped, Base):
    __tablename__ = "knowledge"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="derived")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class PromptDefinition(Timestamped, Base):
    __tablename__ = "prompt_definitions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(Text)


class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    __table_args__ = (
        UniqueConstraint("prompt_definition_id", "version_number", name="uq_prompt_version"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    prompt_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("prompt_definitions.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    prompt_text: Mapped[str] = mapped_column(Text)
    user_instructions: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(255))
    temperature: Mapped[float | None] = mapped_column(Float)
    top_p: Mapped[float | None] = mapped_column(Float)
    max_tokens: Mapped[int | None] = mapped_column(Integer)
    input_schema_version: Mapped[str | None] = mapped_column(String(64))
    output_schema_version: Mapped[str | None] = mapped_column(String(64))
    prompt_hash: Mapped[str] = mapped_column(String(128), index=True)
    schema_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[str] = mapped_column(String(32), default="system")


class PromptTestCase(Timestamped, Base):
    __tablename__ = "prompt_test_cases"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    prompt_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("prompt_definitions.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    input_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    expected_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    assertions_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)


class AiDerivationMeta(Base):
    __tablename__ = "ai_derivation_meta"
    __table_args__ = (UniqueConstraint("object_type", "object_id", name="uq_derivation_object"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    object_type: Mapped[str] = mapped_column(String(64))
    object_id: Mapped[UUID] = mapped_column(Uuid, index=True)
    provider: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(255))
    prompt_name: Mapped[str | None] = mapped_column(String(120))
    prompt_version: Mapped[int | None] = mapped_column(Integer)
    schema_version: Mapped[str | None] = mapped_column(String(64))
    prompt_hash: Mapped[str | None] = mapped_column(String(128))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AskQuery(Base):
    __tablename__ = "ask_queries"
    __table_args__ = (Index("ix_ask_queries_created", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    query_text: Mapped[str] = mapped_column(Text)
    source_scope: Mapped[str] = mapped_column(String(32), default="all")
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIJob(Base):
    __tablename__ = "ai_jobs"
    __table_args__ = (
        UniqueConstraint("entry_id", "job_type", "generation", name="uq_ai_job_generation"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    entry_id: Mapped[UUID] = mapped_column(ForeignKey("entries.id", ondelete="CASCADE"), index=True)
    job_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    provider: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(255))
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    generation: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    token_usage: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
