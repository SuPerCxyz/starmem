## 1. Workbench persistence and routing

- [x] 1.1 Add EntrySafetyScan and SavedSearch models, UserSetting model_routing field and Alembic migration without changing Raw/Memory semantics.
- [x] 1.2 Add schemas and API settings validation for task routes with secret-safe provider/model responses.
- [x] 1.3 Apply route priority in Chat/AI jobs and preserve final provider/model in existing Derivation/Job provenance.

## 2. Local safety and similarity

- [x] 2.1 Extend local secret scanner to return finding type/line/column summaries without retaining matched secret text, and scan Entry create/update/import content.
- [x] 2.2 Add Entry safety status API/UI and a bounded rescan path for existing entries.
- [x] 2.3 Implement advisory similar-entry retrieval using trigram/FTS and optional vector candidates with exact entry/source filtering.
- [x] 2.4 Add similar-entry API and Capture/Timeline display that preserves the current Entry and offers source navigation only.

## 3. Project, Topic and Entity workbench

- [x] 3.1 Add bounded Project/Topic/Entity list and detail services with first/last seen, Entry/Memory counts and related evidence.
- [x] 3.2 Add Project/Topic/Entity API endpoints with empty-data behavior and soft-delete/source filtering.
- [x] 3.3 Build responsive workbench views for Project, Topic and Entity details without making folders mandatory.

## 4. Saved Search and Smart View

- [x] 4.1 Add Saved Search CRUD endpoints with query/filter validation and no result snapshot duplication.
- [x] 4.2 Add stable Smart View definitions for problems, solutions, TODO, decisions, tests/performance, recent changes, unresolved issues, new/conflicted Memory and failed AI jobs.
- [x] 4.3 Build Saved Search/Smart View UI and connect each result to Search, Entry, Memory or Job actions.

## 5. Review and Knowledge Summary

- [x] 5.1 Add bounded review service/API for today, week, month and custom ranges with counts and representative sources.
- [x] 5.2 Add deterministic Knowledge Summary generation for Project/Topic/time scope with Entry/Memory source IDs and regeneration.
- [x] 5.3 Add Workbench review/summary UI and source navigation while keeping Knowledge derived and Atomic Memory independent.

## 6. Tests, documentation and verification

- [x] 6.1 Add backend tests for safety scans, user overrides, similarity fallback, workbench aggregation, Saved Search/Smart View, routing precedence and Knowledge provenance.
- [x] 6.2 Add browser tests for workbench navigation, save/delete search, source jumps, safety notices and responsive layout.
- [x] 6.3 Update README/operations/phase documentation with route configuration, privacy behavior, rebuild/rescan and known limits.
- [x] 6.4 Run migration/seed, formatter/lint, backend tests, Web build, integration smoke and browser checks; clean test fixtures.
- [x] 6.5 Validate OpenSpec strictly and review scope, credentials, generated files and behavior against the confirmed P1 boundary.
