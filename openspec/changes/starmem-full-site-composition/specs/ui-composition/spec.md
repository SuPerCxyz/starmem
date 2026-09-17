## Purpose

让 StarMem 的每个用户可访问页面都具备可识别的任务结构、完整的状态反馈和一致的桌面/移动体验，并以固定的 Preline Composition 作为页面级视觉来源。

## ADDED Requirements

### Requirement: All user-accessible surfaces have a page composition

StarMem SHALL enumerate every public, authenticated, logical workspace, nested detail surface, management child surface, modal-driven detail surface, and unknown-path error surface in the page inventory. Each enumerated surface SHALL be assigned exactly one of the six page masters: Capture Workspace, Browse Workspace, Search Workspace, AI Workspace, Detail Workspace, or Management Workspace; Auth and Error surfaces SHALL be documented variants of those masters.

#### Scenario: A new route is added
- **WHEN** a new user-accessible route or nested surface is introduced
- **THEN** the page inventory contains its route, master, Preline source mapping, desktop/mobile layout, and Empty/Loading/Error/Loaded states before the implementation is considered complete

#### Scenario: Existing logical pages are audited
- **WHEN** the application exposes a page through navigation, a detail action, a management action, a modal, or a direct URL
- **THEN** that surface appears in the inventory and has a completion status that cannot be omitted from the final audit

### Requirement: The application shell is compositionally consistent

All authenticated workspaces SHALL use one responsive Application Shell with the StarMem brand, grouped navigation for real capabilities, a consistent content header, account/system actions, mobile off-canvas navigation, and no more than five mobile bottom-navigation destinations. A page SHALL NOT implement a competing sidebar, header, container, or navigation system.

#### Scenario: Navigate between authenticated pages
- **WHEN** a user switches between Capture, Browse, Search, AI, Detail, or Management surfaces
- **THEN** the shell, active navigation state, responsive behavior, theme tokens, and account actions remain consistent while the page composition changes

#### Scenario: Open the application on a supported mobile viewport
- **WHEN** the viewport is 390px or 430px wide
- **THEN** the off-canvas shell, header, bottom navigation, safe-area insets, and page content remain usable without horizontal overflow

### Requirement: Page masters expose task-complete states

Each page master SHALL provide a task-specific Page Header and SHALL represent Empty, Loading, Error, and Loaded states with understandable copy and an applicable recovery, navigation, or primary action. A loaded state SHALL use real StarMem data and SHALL NOT add fabricated metrics or placeholder modules to fill space.

#### Scenario: A page has no data
- **WHEN** its API returns an empty collection or the user has not started the task
- **THEN** the page shows a complete Empty State with a truthful explanation and a relevant next action or suggestion

#### Scenario: A page request fails
- **WHEN** a page or detail request returns an error
- **THEN** the page shows a Preline-token-based error surface with understandable feedback and Retry or return behavior where recovery is applicable

#### Scenario: A page request is pending
- **WHEN** a page is waiting for API data
- **THEN** the page shows a stable skeleton, spinner, or placeholder composition and does not collapse into unrelated blank space

### Requirement: Management and detail capabilities are discoverable

Existing management and detail capabilities SHALL be presented as dedicated, navigable compositions rather than one undifferentiated long page or an unstructured field dump. Entry, Memory, Workbench object, Prompt, AI Job, Inbox/Source provenance, and version surfaces SHALL expose their primary content, metadata, related evidence, history or processing information, and applicable actions using a desktop rail and a mobile stack or Drawer where appropriate.

#### Scenario: A user opens a management capability
- **WHEN** the user selects Settings, Model/Provider, Prompt Studio, Prompt History, Prompt Tests, AI Jobs, Memory, Backup/Import, Inbox, Workbench, or Source browsing
- **THEN** the selected capability has its own page-level heading, navigation context, content workspace, real data state, and action feedback without requiring unrelated sections to remain visible above or below it

#### Scenario: A user opens a detail surface
- **WHEN** the user selects an Entry, Memory, Workbench object, Prompt version, or AI Job
- **THEN** the detail surface presents primary content and provenance/metadata in a clear main-and-rail desktop composition and an accessible mobile Drawer or stacked equivalent, with close/back and recovery actions

### Requirement: Preline is the only page visual source

All page-level structure, visual tokens, forms, list/table patterns, overlays, upload patterns, status treatments, and icon usage SHALL be traceable to the pinned Preline reference or an existing StarMem mapping. If no direct free Composition exists, the implementation SHALL use the closest real Preline source and record the deviation in the source map; it SHALL NOT create a second design system or introduce arbitrary visual values.

#### Scenario: Review a page implementation
- **WHEN** an auditor opens the page inventory and source map for any completed surface
- **THEN** the page has a concrete Preline file/block/component reference and no undocumented custom visual system

#### Scenario: Scan new frontend styling
- **WHEN** `web/src` is scanned for hard-coded colors, arbitrary visual Tailwind values, competing UI libraries, or custom card/button/sidebar primitives
- **THEN** the scan finds no new violations attributable to this change
