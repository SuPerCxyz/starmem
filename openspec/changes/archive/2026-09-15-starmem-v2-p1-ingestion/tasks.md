## 1. Runtime and persistence foundation

- [x] 1.1 Add attachment storage, upload limits, URL limits, OCR settings, shared Docker storage volume and required Python/runtime dependencies.
- [x] 1.2 Add Attachment model and migration; extend IngestionJob with Entry/Attachment links, input kind, idempotency key, phase, metadata and error lifecycle without breaking P0 external sync rows.
- [x] 1.3 Add authenticated attachment metadata/download schemas and filesystem storage helpers with UUID keys, SHA-256 verification and path traversal protection.

## 2. Input parsing and safe fetching

- [x] 2.1 Implement bounded UTF-8/fallback text decoding and format detection for TXT, Markdown, JSON, YAML and Log files.
- [x] 2.2 Implement PDF extraction into ordered page records with page metadata and scanned-page OCR fallback.
- [x] 2.3 Implement local Tesseract OCR Provider for images/PDF pages with language configuration, timeout/error reporting and no remote Chat path.
- [x] 2.4 Implement safe HTTP/HTTPS URL fetching with redirect, DNS/IP, status, content-type, byte-size and timeout limits plus lightweight HTML title/body extraction.

## 3. Ingestion workflow and worker

- [x] 3.1 Implement unified URL/file import services that persist the Native Entry, attachment/URL metadata and IngestionJob before enqueueing processing.
- [x] 3.2 Implement idempotent asynchronous ingestion Worker processing for text, PDF, image OCR and URL snapshots; update Entry versions/ContentUnits and enqueue existing chunk/embedding/AI jobs.
- [x] 3.3 Implement status transitions, attempt locking, deterministic errors and safe retry behavior without duplicating Entry, Attachment or derived units.
- [x] 3.4 Preserve page/OCR/URL metadata in ContentUnit and Search/Ask provenance, including attachment identifiers and page numbers.

## 4. API and Inbox

- [x] 4.1 Add authenticated `POST /api/v1/ingest/url` and multipart `POST /api/v1/ingest/file` endpoints with validation and `Idempotency-Key` support.
- [x] 4.2 Add Inbox list/detail/filter/retry endpoints and attachment metadata/download endpoints with bounded response metadata and secret-safe errors.
- [x] 4.3 Add API tests for accepted formats, unsupported/oversized input, URL SSRF/redirect limits, idempotency, PDF pages, OCR success/failure and retry/concurrency.

## 5. Web experience

- [x] 5.1 Add Capture input mode for URL/file upload while preserving the existing text Capture path and draft behavior.
- [x] 5.2 Add Inbox UI for New/Processing/Processed/Failed states, error details, retry, Entry opening and attachment/page source metadata.
- [x] 5.3 Add responsive attachment/source status styles and verify no secret, raw file bytes or horizontal overflow is exposed in the UI.

## 6. Operations, documentation and verification

- [x] 6.1 Include attachment storage in backup/restore scripts and document volume, size limits, OCR dependencies, recovery and orphan cleanup.
- [x] 6.2 Add integration fixtures for text/PDF/image/URL imports and verify imported content flows through Timeline, Search, Ask and Source navigation.
- [x] 6.3 Run formatter/lint, backend tests, migration/seed, Compose smoke, Web build and responsive/browser checks; record actual results and known OCR/device limits.
- [x] 6.4 Validate this OpenSpec change strictly and review scope, credentials, generated files and test data before marking the change complete.
