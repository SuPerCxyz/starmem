## 1. Share Target contract

- [x] 1.1 Add manifest Share Target metadata for text, URL, image and file content.
- [x] 1.2 Add bounded IndexedDB share payload helper with delete-after-read behavior.
- [x] 1.3 Extend Service Worker to receive same-origin `/share` multipart requests and redirect to Capture.

## 2. Capture integration

- [x] 2.1 Read shared payload on app startup and prefill text/URL/file Capture modes.
- [x] 2.2 Add share success, cancellation, oversize and storage-unavailable feedback without changing normal Capture.
- [x] 2.3 Preserve existing URL/file upload, CSRF, OCR and attachment flows.

## 3. Tests and docs

- [x] 3.1 Add unit/browser checks for manifest, Share Target payload, text/URL prefill and bounded file handling.
- [x] 3.2 Run Web build, backend regression, responsive browser checks and clean temporary shared fixtures.
- [x] 3.3 Document mobile Share Target behavior and limitations; validate OpenSpec scope and security boundary.
