## 1. Audit and reference baseline

- [x] 1.1 Update `PRELINE_SOURCE_MAP.md` with the pinned Preline commit, concrete shell/composer/overlay/upload/management references, and deviations.
- [x] 1.2 Complete `STARMEM_PAGE_INVENTORY.md`, `STARMEM_FULL_SITE_UI_AUDIT.md`, and `UI_COMPOSITION_RULES.md` with the final route/status model and six-master mapping.

## 2. Shared routing, layout, and state primitives

- [x] 2.1 Add the typed history-based route adapter, direct logical page paths, nested detail paths, back navigation, and unknown-path 404 handling without changing API contracts.
- [x] 2.2 Extend shared UI primitives for PageFrame, SectionHeader, LoadingState, ErrorState, EmptyState, FilterBar, responsive DetailRail, and ManagementNav using existing Preline tokens.
- [x] 2.3 Refactor the Application Shell into grouped real-capability navigation with one responsive header, sidebar, bottom navigation, account actions, and active-state behavior.
- [x] 2.4 Add front-end client methods for existing read-only Entry, Memory, Prompt, and AI Job detail endpoints.

## 3. Capture and Browse workspaces

- [x] 3.1 Recompose Capture as a wide Capture Workspace with Composer, recent feed, real feedback, and a Preline-aligned upload/dropzone presentation while preserving text/URL/file behavior.
- [x] 3.2 Recompose Timeline as a wide chronological Browse Workspace with filter scope, date grouping, list/feed density, pagination, and complete states.
- [x] 3.3 Recompose Inbox as a browse/list workspace with processing filters, compact rows, attachment details, correction/retry actions, and complete states.
- [x] 3.4 Recompose Knowledge Workbench as a master/detail Browse Workspace with responsive object navigation, Smart Views, Review, Summary, and truthful management actions.
- [x] 3.5 Add a truthful Source browse surface derived only from existing Entry/Search/Ask provenance and document the absence of connector/sync operations.

## 4. Search and AI workspaces

- [x] 4.1 Recompose Search with wide controls, recent/saved state, filter disclosure, result list, match metadata, preview affordance, no-result state, and responsive layout.
- [x] 4.2 Recompose Ask with Preline AI composer, conversation/answer hierarchy, follow-up suggestions, first-class Sources rail, mobile Sources Drawer, and complete states.

## 5. Management workspaces

- [x] 5.1 Split More into Settings overview, Model/Provider, Backup/Import and batch-operation sections behind ManagementNav, preserving runtime-secret boundaries.
- [x] 5.2 Add AI Jobs list/table composition with status filters, retry actions, real metadata, loading/error/empty states, and AI Job detail surface.
- [x] 5.3 Split Prompt Studio into Prompt list/editor master-detail plus dedicated Version History and Test Cases surfaces, including run status/result/diff presentation.
- [x] 5.4 Promote Memory Lifecycle into a dedicated management list with status filters, actions, and Memory Detail surface containing evidence/source/history fields.

## 6. Detail workspaces

- [x] 6.1 Promote Entry Detail to a direct Detail Workspace with Raw Content main area, Metadata/Provenance/Related rail, actions, and mobile Drawer/stack fallback.
- [x] 6.2 Promote Entry Version History and diff to a direct nested detail surface with accessible close/back, loading, error, empty, and loaded states.
- [x] 6.3 Ensure Workbench object detail, Prompt version detail, Memory detail, AI Job detail, and Ask Sources share the Detail Workspace composition and truthful provenance actions.

## 7. Cross-page quality and compatibility

- [x] 7.1 Remove page-level visual duplication and stale custom composition, preserving existing accessible labels, IDs, business hooks, API payloads, and Preline-only visual rules.
- [x] 7.2 Verify Empty/Loading/Error/Loaded states, light/dark themes, focus and touch behavior, no horizontal overflow, and 390/430/768/1024/1440/1920 layouts across every inventory row.
- [x] 7.3 Update browser traversal/smoke selectors only where structure intentionally changed, and exercise direct routes, navigation, back/close, retries, uploads, filters, and management actions.

## 8. Final evidence and handoff

- [x] 8.1 Build and run the proportionate API/Web/Playwright checks; capture the required desktop and mobile screenshots with console/page-error evidence.
- [x] 8.2 Update Inventory statuses to `completed`, finalize Audit and `STARMEM_FULL_SITE_COMPOSITION_REPORT.md`, and validate OpenSpec artifacts with no unexplained incomplete item.
