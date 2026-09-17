## 1. Tabler baseline and vendor evidence

- [x] 1.1 Clone/pull the official Tabler repository, record the pinned commit/version/clone time, and run the repository-defined install/build commands.
- [x] 1.2 Run the official Tabler preview and capture the required layout, search, settings, chat, activity, tables, auth, and error reference screenshots.
- [x] 1.3 Copy the unmodified official CSS/JS/icon/font assets produced by the pinned build into the StarMem vendor path and record SHA-256 checksums.
- [x] 1.4 Complete `TABLER_SOURCE_MAP.md`, `TABLER_VENDOR_INFO.md`, `TABLER_DEVIATIONS.md`, and the full Route Inventory with Tabler source files, DOM sections, class fidelity, and status.

## 2. Front-end visual-system switch

- [x] 2.1 Remove Preline/Lucide/Tailwind visual dependencies from the web package and install the pinned official Tabler Icons React package without changing business dependencies.
- [x] 2.2 Replace the CSS entry with the read-only vendor Tabler CSS and retain only documented safe-area, browser/PWA, overflow, and reduced-motion integration rules.
- [x] 2.3 Replace Preline theme/bootstrap initialization with Tabler official theme attributes, localStorage keys, ESM JavaScript and Bootstrap data API initialization.
- [x] 2.4 Replace the icon wrapper implementation with official Tabler icon components while preserving existing semantic imports and accessible labels.

## 3. Tabler application shell and shared compositions

- [x] 3.1 Rebuild the Application Shell from Tabler vertical navbar/page/page-wrapper/page-header/page-body/container-xl markup with grouped real navigation and footer account area.
- [x] 3.2 Rebuild shared PageHeader, PageFrame, FilterBar, EmptyState, LoadingState, ErrorState, DetailRail, Status and ManagementNav outputs with official Tabler class combinations.
- [x] 3.3 Preserve direct route parsing, nested route navigation, back/close behavior, responsive offcanvas/collapse targets and the existing cropped StarMem logo asset.
- [x] 3.4 Add focused render/route checks proving the Shell and shared compositions contain no Preline `hs-*`, Tailwind visual utilities or custom visual selectors.

## 4. Capture and browse workspaces

- [x] 4.1 Migrate Record/Capture to Tabler page-header/card/form-control/input-group/btn/dropdown and official file/dropzone composition while preserving text, URL, file, image, drag/drop and progress behavior.
- [x] 4.2 Migrate Timeline and Recent Records to Tabler activity/timeline/list-group/card-list/divider patterns with filters, date grouping, pagination and all states.
- [x] 4.3 Migrate Import Inbox to Tabler list-group/table/form/status patterns with correction, retry, attachment details and mobile responsive rows.
- [x] 4.4 Migrate Knowledge Workbench and Sources to Tabler row/col/list/card/master-detail patterns using only real projects/topics/entities/provenance data.

## 5. Search, AI and detail workspaces

- [x] 5.1 Migrate Search no-query/results/no-results states to the official search-results/list/table/empty patterns with filters, saved searches and match metadata.
- [x] 5.2 Migrate Ask conversation, prompt suggestions, follow-up, answer and Sources rail/offcanvas to official Tabler chat/chat-bubbles/chat-bubble/list patterns.
- [x] 5.3 Migrate Entry and version history to Tabler card/datagrid/list-group/tabs/timeline detail compositions with raw content, metadata, provenance and actions.
- [x] 5.4 Migrate Memory, Workbench object details and Source detail to Tabler datagrid/list/status/timeline compositions with evidence/history/relations.

## 6. Management, auth and error surfaces

- [x] 6.1 Migrate Settings overview, Model Provider and Backup/Import to Tabler settings/form/fieldset/alert/upload compositions with runtime-secret boundaries.
- [x] 6.2 Migrate Prompt Studio, version history and tests to Tabler master-detail/tabs/form/table/badge/alert compositions with real run status, expected/actual/diff and actions.
- [x] 6.3 Migrate AI Jobs list/detail and Memory management to Tabler table/list/datagrid/status/detail compositions with filters, retry and truthful metadata.
- [x] 6.4 Migrate Login and 404/error/loading surfaces to the closest official Tabler auth/empty/error/alert compositions without adding a custom visual system.

## 7. Interaction, responsive and regression verification

- [x] 7.1 Update Playwright smoke/traversal/composition selectors for Tabler DOM and exercise capture/import, filters, search, ask/sources, detail back/close, retries, management actions and auth/error flows.
- [x] 7.2 Run route matrix QA at 390×844, 430×932, 768, 1024, 1440×1000 and 1920×1080 for light/dark themes, console/page errors, focus/touch interactions and horizontal overflow.
- [x] 7.3 Run API tests, ruff, StarMem Web build, Compose Web build and integration smoke; distinguish pre-existing failures from migration failures.
- [x] 7.4 Run CSS/vendor/Preline/Tailwind/inline-style/hardcoded-color audits and verify vendor files are unchanged from the pinned Tabler build checksum.

## 8. Final handoff

- [x] 8.1 Capture final StarMem desktop/mobile screenshots and pair them with the official Tabler reference screenshots in the migration report.
- [x] 8.2 Update all Inventory statuses to `completed`, finalize `STARMEM_TABLER_MIGRATION_REPORT.md`, `DEVELOPMENT_STATUS.md`, and validate OpenSpec with no unexplained incomplete task.
