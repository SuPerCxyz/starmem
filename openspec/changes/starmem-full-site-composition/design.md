## Context

See `proposal.md` for motivation and `specs/ui-composition/spec.md` for the observable contract. The current React client renders seven logical pages from one `Workspace` switch, keeps detail surfaces in local Drawers, and concentrates management features in `MorePage`. The existing Preline tokens, inline icon set, query client, and API client are the stable implementation base.

## Goals / Non-Goals

**Goals:**

- Establish a small route adapter over the current single-page state so authenticated pages and existing detail APIs can be opened directly without introducing a router dependency.
- Keep one Application Shell and add grouped navigation for real capabilities only.
- Extract shared page primitives and status patterns, then compose each page according to the six masters.
- Split management content into navigable Settings, Models, Prompts, Jobs, Memory, Backup, and Sources surfaces while preserving mutations and API payloads.
- Promote Entry, Workbench object, Memory, Prompt version, and AI Job details into clear main/rail or mobile Drawer compositions.
- Use pinned Preline blocks/tokens as evidence and retain the project’s existing theme and icon system.

**Non-Goals:**

- No new backend endpoints, database tables, migrations, worker behavior, connector sync, CLI/MCP, or multi-user capability.
- No fake source synchronization, dashboard KPIs, or data added only to fill whitespace.
- No replacement of the existing business API contract or Raw-first behavior.
- No new visual dependency or standalone design system.

## Decisions

### 1. Use a small history-based route adapter instead of adding a router

The app already owns page state and has no route tree. A small typed route parser/writer around `window.history` keeps the dependency surface unchanged, enables `/capture`, `/timeline`, `/search`, `/ask`, `/settings/*`, `/entries/:id`, `/workbench/:kind/:id`, `/sources`, and a real unknown-path surface, and preserves the existing in-memory navigation callbacks. React Router was considered but would require moving every existing stateful page into route elements without improving the composition itself.

### 2. Keep business page state local, move shared visual structure to primitives

`PageHeader`, `FilterBar`, `EmptyState`, `LoadingState`, `ErrorState`, `SectionHeader`, `ManagementNav`, and detail layout helpers will remain token-only primitives. Query/mutation state stays with the page that owns the behavior, avoiding a speculative global store while making visual composition consistent.

### 3. Use one management page with URL-addressable sections

The current More state contains related management behaviors and already loads the required APIs. It will become a Management Workspace whose section is selected by route (`settings`, `models`, `prompts`, `jobs`, `memory`, `backup`, `sources`). This avoids duplicating query/mutation logic while preventing the UI from rendering every section as one long card wall.

### 4. Treat source management as truthful provenance browsing

There is no source-list or connector-sync endpoint. The Source surface will derive unique source IDs/URIs and counts from real Entry/Search/Ask provenance when available, and explicitly state that connector synchronization is not configured. It will not invent provider status or management mutations.

### 5. Preserve compatibility selectors and interaction contracts

Existing accessible labels, IDs, `entry-card`/`entry-content`/`entry-meta`/`entry-ai-steps` hooks, navigation labels, and mutation payloads will remain available while composition classes change. Existing smoke/traversal tests will be updated only where they asserted obsolete structural selectors; business-path assertions remain unchanged.

### 6. Prefer Preline list, divider, table, overlay, and upload structures

The implementation will reuse the pinned centered AI workspace for shell/composer, the dashboard template for management grids, the overlay README for Drawer ARIA/structure, and the file-upload README for dropzone semantics. Where the pinned repository has no direct free Auth or Source page, the closest Preline form/list composition and a documented deviation will be used.

## Risks / Trade-offs

- [Risk] A route adapter can desynchronize browser history and in-memory page state. → Centralize parse/write/popstate handling and exercise direct URLs, back navigation, and unknown paths.
- [Risk] Splitting More may hide a mutation or invalidate the wrong query. → Keep existing API calls, query keys, and mutation callbacks in their owning section; run traversal across each management section.
- [Risk] Derived Source browsing is bounded by the Entry list page and lacks a backend source contract. → Label it as provenance browsing, cap/indicate the snapshot scope, and do not claim connector management.
- [Risk] Existing Preline package does not include every requested free page block. → Record each closest-source deviation in `PRELINE_SOURCE_MAP.md`; do not recreate a visual system.
- [Risk] Large existing `main.tsx` makes partial edits easy to break. → Extract only stable page/layout components where it reduces risk, build after each vertical slice, and keep API behavior unchanged.

## Migration Plan

1. Complete the route inventory, source map, and audit baseline.
2. Add shared states/layout primitives and the grouped shell.
3. Refactor Capture/Browse/Search/AI compositions without changing API calls.
4. Split Management sections and add real detail surfaces/route aliases.
5. Add/update browser traversal for empty/loading/error/loaded and direct routes.
6. Build the Web image, run API-independent and full browser checks, capture required desktop/mobile screenshots, update reports, and leave the current Compose service on the rebuilt Web image.

Rollback is file-level: revert the front-end/docs change and rebuild the Web image; no data migration or backend rollback is required.
