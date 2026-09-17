## 1. Relations and metadata curation

- [x] 1.1 Add relation read service and `GET /api/v1/entries/{entry_id}/relations` returning outbound/inbound relations with target Entry summary, type, confidence and source.
- [x] 1.2 Add Entry detail 「相关记录」 UI with jump targets and empty/error states.
- [x] 1.3 Add metadata update service for content type, Summary, Project, Topic and Importance that writes user-observation marks and skips AI overwrite.
- [x] 1.4 Extend AI persistence to skip user-locked observations, user-confirmed tags and user-sourced entities during reprocessing.
- [x] 1.5 Add Metadata editing panel in Entry detail covering tags, type, project, topic, summary, entity and importance with user-visible lock indication.
- [x] 1.6 Add Project/Topic rename, merge, exclude and Entity merge services plus authenticated API endpoints with audit metadata.
- [x] 1.7 Add Workbench UI actions for rename/merge/exclude and verify excluded items leave default lists without deleting evidence.

## 2. Inbox correction and image description

- [x] 2.1 Add `PATCH /api/v1/inbox/{job_id}` to correct title and content type, writing an EntryVersion and preserving attachments/provenance.
- [x] 2.2 Add Inbox correction UI with validation feedback and re-fetch of corrected Entry.
- [x] 2.3 Add `ImageDescriptionProvider` contract, configuration flag and local/remote implementations with bounded timeout.
- [x] 2.4 Add `image_describe` AI job and persistence into observations, with OCR-only fallback and explicit degradation reason when unavailable.

## 3. Batch reprocessing, reranker and ask analytics

- [x] 3.1 Add bounded batch reprocess API (explicit IDs or filters, max 200) reusing generation-unique jobs and reporting submitted/failed counts.
- [x] 3.2 Add maintenance endpoint and documentation for full-library Embedding rebuild.
- [x] 3.3 Add batch reprocess and rebuild UI in More/Workbench with confirmation and result feedback.
- [x] 3.4 Add configurable Reranker provider (default disabled), Hybrid rerank step with metric and automatic fallback.
- [x] 3.5 Add `ask_queries` migration, redacted query logging and bounded aggregation.
- [x] 3.6 Add「最近常问」Smart View backed by ask analytics with empty-data and limit behavior.

## 4. Performance, documentation and lifecycle

- [x] 4.1 Add `scripts/benchmark.py` measuring Raw save, FTS, Hybrid and Ask local retrieval with configurable scale and JSON output.
- [x] 4.2 Run the benchmark at an achievable scale, record actual numbers and document any 100k/500k degradation honestly.
- [x] 4.3 Backfill the P0 completion checklist, add the Performance section to the P0 report and update README/DEVELOPMENT_STATUS/phase docs.
- [x] 4.4 Add backend tests for relations, metadata lock semantics, project/topic management, Inbox correction, image description fallback, batch reprocess, reranker fallback and ask analytics.
- [x] 4.5 Add Playwright coverage for relations, metadata editing, Inbox correction, batch actions and「最近常问」.
- [x] 4.6 Run formatter/lint, backend tests, migration/seed, Compose smoke, Web build, Playwright and record actual results.
- [x] 4.7 Archive the five completed changes with main spec sync, validate this change strictly and review scope, credentials, generated files and test data.
