## 1. Repository and runtime foundation

- [x] 1.1 Create backend, web, worker, migrations, prompts, tests, scripts, docker and docs/implementation directories without copying the credential into any file.
- [x] 1.2 Add Python and frontend dependency manifests, `.env.example`, `.gitignore`, formatting/lint/test configuration and local development commands.
- [x] 1.3 Add Docker Compose services for web, api, worker, PostgreSQL with pgvector/pg_trgm and Redis, plus health checks and persistent volumes.
- [x] 1.4 Initialize FastAPI, React/Vite and Worker entrypoints with request IDs, structured logging and a `/health` endpoint that checks API, database and Redis.
- [x] 1.5 Implement single-user bootstrap, password hashing, database sessions, HttpOnly/SameSite/Secure cookie configuration, CSRF checks, CORS allowlist, rate limiting and API token authentication.
- [x] 1.6 Add the initial Alembic migration framework and a reproducible migration/seed command.
- [x] 1.7 Add `StarMem Native` seed data, default configuration handling and a smoke test that starts the stack and checks health.

## 2. Core data model and source boundaries

- [x] 2.1 Implement SQLAlchemy models for users, sessions, entries, entry versions, content units, entry chunks and AI jobs.
- [x] 2.2 Implement models for tags, entry tags, entities, entry entities, projects, topics, observations, memories, memory sources, relations, knowledge and AI derivation metadata.
- [x] 2.3 Implement Source, External Item and ingestion job models with generic external identifiers, hashes, cursors, sync timestamps and retry state.
- [x] 2.4 Add database indexes and constraints for soft deletion, normalized tags/entities, source ownership, ContentUnit lookup, job idempotency and Memory scopes.
- [x] 2.5 Add the ExternalSourceAdapter Protocol with discover/fetch/normalize/get_cursor contracts and a test fixture adapter only; do not implement a real Connector.
- [x] 2.6 Add tests for Native Source linkage, External fixture read-only behavior, ContentUnit ownership and idempotent external snapshots.

## 3. Phase 1 Raw Memory

- [x] 3.1 Implement Entry create/list/get/update/delete APIs with optional title, format/type, pin, favorite, importance, event time and soft deletion.
- [x] 3.2 Make Entry creation transactionally persist raw content, EntryVersion, Native Source, initial ContentUnit and AI job records before returning.
- [x] 3.3 Implement version creation, history listing, diff and restore while preserving immutable historical content.
- [x] 3.4 Implement cursor-based Timeline queries with date grouping, date presets, date range, pin/favorite and default soft-delete filtering.
- [x] 3.5 Implement PostgreSQL tsvector/GIN search, pg_trgm/ILIKE fallback, snippets, highlighting and filters for technical identifiers and metadata.
- [x] 3.6 Build the Capture and Timeline Web pages with Markdown/code rendering, copy action, optional metadata, edit/delete/pin/favorite controls and AI status placeholders.
- [x] 3.7 Add Phase 1 API/model/UI tests for AI-down capture, 20,000+ character preservation, Markdown/code preservation, WWN exact search, three edits and soft delete.
- [x] 3.8 Write `docs/implementation/phase-1.md` with actual migration, API, UI, test and known-limit results; do not advance until Phase 1 tests pass.

## 4. Phase 2 Chunk, Embedding and Search

- [x] 4.1 Implement structure-aware chunking for headings, prose, code, logs, lists, tables, JSON and YAML with code/traceback preservation.
- [x] 4.2 Implement ChatProvider, EmbeddingProvider and RerankerProvider protocols plus Mock providers used by tests.
- [x] 4.3 Implement lazy FastEmbed provider using configurable `BAAI/bge-small-zh-v1.5` and dimension validation, with clear unavailable-model errors and no Raw/FTS blockage.
- [x] 4.4 Add pgvector storage and indexes for Chunk and Memory embeddings, embedding rebuild commands and provider timeout handling.
- [x] 4.5 Implement semantic search with chunk score, snippet and capability status; implement configurable Full Text + Vector Hybrid candidate merge.
- [x] 4.6 Implement query identifier detection and exact IP/UUID/WWN/hostname/domain/path/error/model boost ahead of semantic similarity.
- [x] 4.7 Implement source scope filters for all/native/external/specific Source in search queries.
- [x] 4.8 Add Phase 2 fixed datasets and tests for Chinese paraphrase recall, causal hybrid ranking, exact identifier priority, chunk boundaries and missing Embedding fallback.
- [x] 4.9 Write `docs/implementation/phase-2.md` with actual benchmark and test results; do not advance until Phase 2 tests pass or an environment limitation is explicitly recorded.

## 5. Phase 3 AI Enrichment and Prompt Engine

- [x] 5.1 Add built-in Prompt resources for observation, classification, summary, tag, entity, temporal, project, topic, relation, memory, salience, reconcile, query and answer tasks.
- [x] 5.2 Implement Prompt Definition, Prompt Version, Prompt Test Case and AI Derivation Metadata persistence plus seed synchronization.
- [x] 5.3 Implement OpenAI-compatible ChatProvider using runtime API key, bounded timeout/retries/backoff and `chat_template_kwargs.enable_thinking=false` by default; add `docs/LOCAL_LLM.md` without the key.
- [x] 5.4 Implement layered Prompt resolution, immutable safety contract, editable User Instructions, Draft/Testing/Production/Archived status and prompt hash calculation.
- [x] 5.5 Implement Prompt preview, version history, diff, rollback, promote, restore default and built-in/user test case endpoints.
- [x] 5.6 Implement strict Pydantic output schemas and JSON extraction; mark invalid output as Prompt Validation Failed and do not persist derived data.
- [x] 5.7 Implement independent idempotent AI Job records/handlers for summary, classification, tags, entities, temporal data, projects/topics, relations and embeddings.
- [x] 5.8 Implement deterministic identifier/time extraction and user-source precedence for tags/entities/metadata.
- [x] 5.9 Build AI Job list/detail/retry UI, Prompt Studio UI and metadata panels for Entry/Memory provenance.
- [x] 5.10 Add Golden Dataset and Mock Provider tests for valid/invalid output, provider timeout, retry, idempotency, user overrides and Draft isolation.
- [x] 5.11 Write `docs/implementation/phase-3.md` and block Phase 4 until Phase 3 tests pass.

## 6. Phase 4 Memory Engine

- [x] 6.1 Implement Observation and Memory Candidate persistence separate from Evidence/Raw Entry, including generation metadata and salience fields.
- [x] 6.2 Implement durable/episodic/ignore salience evaluation with temporal fields and deterministic handling of temporary phrases.
- [x] 6.3 Implement Retrieve-Before-Write by subject/predicate/value, normalized keys, entity and semantic candidate lookup.
- [x] 6.4 Implement deterministic Reconcile validation restricted to ADD, SUPPORT, SUPERSEDE, CONFLICT, MERGE and IGNORE.
- [x] 6.5 Implement transactional Memory Apply with PostgreSQL advisory scope locks, unique active constraints, supporting/contradicting sources and history preservation.
- [x] 6.6 Implement Superseded, Conflicted, Expired and Deleted lifecycle queries and manual conflict confirmation/update endpoints.
- [x] 6.7 Implement relation/knowledge derivation hooks without replacing Atomic Memory or Evidence.
- [x] 6.8 Add tests for durable 150W, episodic 175W, support deduplication, 180W→150W supersede, ambiguous 8080/8081 conflict and concurrent workers.
- [x] 6.9 Write `docs/implementation/phase-4.md` and block Phase 5 until Phase 4 tests pass.

## 7. Phase 5 Ask and source-grounded RAG

- [x] 7.1 Implement rule/regex Query Understanding for intent, keywords, identifiers, entities, time hints and answer mode before optional model use.
- [x] 7.2 Implement temporal retrieval presets and bias for recent/first/latest/past-month/year expressions.
- [x] 7.3 Implement candidate context building from Search/Memory/ContentUnit with source scope and bounded snippets.
- [x] 7.4 Implement optional Reranker provider and source-grounded Chat answer generation with facts/inference labels and no-source refusal.
- [x] 7.5 Implement `POST /api/v1/ask` response schema with answer, confidence, sources, Entry IDs, timestamps, snippets, scores and jump targets.
- [x] 7.6 Build Ask UI with separated Answer/Sources sections, follow-up input, source expansion, navigation to highlighted Raw Entry and inference badges.
- [x] 7.7 Add Ask tests for V100 current value, superseded history exclusion, temporal/entity retrieval, native/external citations and unavailable Chat fallback.
- [x] 7.8 Write `docs/implementation/phase-5.md` and block Phase 6 until Phase 5 tests pass.

## 8. Phase 6 P0 polish and operations

- [x] 8.1 Complete responsive desktop/mobile shell at 375px, 768px, 1024px and 1440px with sidebar, mobile bottom navigation, touch targets, focus states and reduced-motion behavior.
- [x] 8.2 Add PWA manifest, standalone metadata, app icons, Safe Area CSS, Service Worker registration placeholder and long-content overflow protection.
- [x] 8.3 Add draft persistence/recovery for refresh, backgrounding and short network interruptions; keep authentication in HttpOnly session cookie.
- [x] 8.4 Add settings for Provider configuration, model routing, AI status, source scope, global instructions and reprocess controls without rendering secrets.
- [x] 8.5 Add structured metrics for request/job/search/embedding/provider latency and token usage with secret-safe logging.
- [x] 8.6 Add `scripts/backup.sh`, `scripts/restore.sh`, database/config backup documentation and embedding rebuild documentation.
- [x] 8.7 Add full integration smoke test for Capture → Job → Timeline → Search → Ask → Source navigation and soft-delete recovery.
- [x] 8.8 Run frontend build/lint and Playwright responsive checks; record that physical iPhone Safari/Home Screen installation remains device-only validation.
- [x] 8.9 Write `docs/implementation/phase-6.md` and `docs/P0_COMPLETION_REPORT.md` from actual command/test/benchmark results.
- [x] 8.10 Validate OpenSpec artifacts against implementation and perform final scope/security/temporary-file review; archive only after P0 is genuinely complete.
