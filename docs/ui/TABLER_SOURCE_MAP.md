# StarMem → Tabler UI 源码映射

## Source of Truth

| 项 | 值 |
| --- | --- |
| Repository | `https://github.com/tabler/tabler.git` |
| Commit | `0776b88863690c9740d7d33988a8b5df66aad6dc` |
| Version | `1.5.1` |
| Clone time | `2026-09-16 17:24:21 +0800` |
| Local source | `.reference/tabler` |
| Official build | `pnpm install --frozen-lockfile && pnpm run build` |
| Production CSS | `web/src/vendor/tabler/tabler.css`、`tabler-vendors.css`、`dropzone.css`，来自官方 `core/dist` 构建产物 |
| Production JS | `web/src/vendor/tabler/tabler.esm.js`，来自 `core/dist/js/tabler.esm.js` |
| Theme JS | `web/src/vendor/tabler/tabler-theme.esm.js`，来自 `core/dist/js/tabler-theme.esm.js` |
| Icons | `@tabler/icons-react@3.46.0` |
| Reference screenshots | `docs/ui/reference/tabler/` |

## 官方参考页面

| 参考截图 | 官方页面 | 主要源码 |
| --- | --- | --- |
| `layout-vertical.png` | `layout-vertical.html` | `.reference/tabler/preview/pages/layout-vertical.astro`、`shared/layouts/DefaultLayout.astro`、`shared/components/navbar/Sidebar.astro` |
| `search-results.png` | `search-results.html` | `.reference/tabler/preview/pages/search-results.astro`、`docs/content/ui/components/list-group.mdx` |
| `settings.png` | `settings.html` | `.reference/tabler/preview/pages/settings.astro`、`shared/layouts/SettingsLayout.astro` |
| `chat.png` | `chat.html` | `.reference/tabler/preview/pages/chat.astro`、`docs/content/ui/components/chat.mdx` |
| `activity.png` | `activity.html` | `.reference/tabler/preview/pages/activity.astro`、`docs/content/ui/components/timeline.mdx` |
| `tables.png` | `tables.html` | `.reference/tabler/preview/pages/tables.astro`、`docs/content/ui/components/table.mdx` |
| `auth.png` | `sign-in.html` | `.reference/tabler/preview/pages/sign-in.astro`、`shared/components/cards/SignInCard.astro`、`shared/layouts/SingleLayout.astro` |
| `error-page.png` | `error-404.html` | `.reference/tabler/preview/pages/error-404.astro`、`docs/content/ui/components/empty.mdx` |
| `dropzone.png` | `dropzone.html` | `.reference/tabler/preview/pages/dropzone.astro`、`docs/content/ui/plugins/dropzone.mdx` |

## StarMem 页面映射

| StarMem Route / surface | StarMem Page | Target Pattern | Tabler Source Page | Tabler Source File | DOM sections used | Allowed business changes | CSS/Class deviations | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/`, `/capture` | Login / Capture | Single / Capture | `sign-in.html`, `layout-vertical.html`, `dropzone.html` | `SingleLayout.astro`, `DefaultLayout.astro`, `preview/pages/dropzone.astro`, `docs/content/ui/plugins/dropzone.mdx` | `.page`, `.page-header`, `.page-body`, `.container-xl`, `.card`, `.form-control`, `.btn`, `.dropzone`, `.dz-message` | text, fields, API events, routes, file/drop behavior | Logo/runtime glue; Dropzone API handler glue | completed |
| `/timeline` | Timeline | Browse / Activity | `activity.html` | `preview/pages/activity.astro`, `docs/content/ui/components/timeline.mdx` | `.page-header`, `.page-body`, `.container-xl`, `.activity`, `.list-group` | entries, dates, filters, pagination | none planned | completed |
| `/search` | Search | Search results | `search-results.html` | `preview/pages/search-results.astro`, `docs/content/ui/components/list-group.mdx` | `.page-header`, `.input-group`, `.form-control`, `.form-select`, `.card`, `.list-group`, `.empty` | query, filters, saved searches, result data | none planned | completed |
| `/ask`, `/ask/sources` | Ask / Sources | Chat / Offcanvas | `chat.html` | `preview/pages/chat.astro`, `docs/content/ui/components/chat.mdx`, `offcanvas.mdx` | `.chat`, `.chat-bubbles`, `.chat-bubble`, `.card`, `.input-group`, `.offcanvas` | questions, answers, sources, follow-up | mobile panel glue | completed |
| `/inbox` | Import Inbox | Inbox / List | `email-inbox.html` | `preview/pages/email-inbox.astro`, `docs/content/ui/components/list-group.mdx` | `.page-header`, `.list-group`, `.list-group-item`, `.badge`, `.alert` | ingestion data, retry/correction events | none planned | completed |
| `/workbench` | Knowledge Workbench | Dashboard / Master-detail | `layout-vertical.html`, `settings.html` | `shared/layouts/DefaultLayout.astro`, `preview/pages/settings.astro` | `.row`, `.col-*`, `.card`, `.nav`, `.list-group`, `.datagrid` | project/topic/entity data and actions | business master-detail glue | completed |
| `/workbench/:kind/:id` | Workbench Detail | Detail / Datagrid | `profile.html`, `settings.html` | `preview/pages/profile.astro`, `shared/layouts/SettingsLayout.astro`, `docs/content/ui/components/datagrid.mdx` | `.page-header`, `.card`, `.datagrid`, `.list-group`, `.nav-tabs` | object summary, relations, history | none planned | completed |
| `/sources` | Source Management | Browse / List-detail | `email-inbox.html`, `settings.html` | `preview/pages/email-inbox.astro`, `preview/pages/settings.astro` | `.card`, `.list-group`, `.list-group-item`, `.datagrid` | real provenance only | no connector/sync UI | completed |
| `/settings` | Settings Overview | Settings | `settings.html` | `preview/pages/settings.astro`, `shared/layouts/SettingsLayout.astro` | `.page-header`, `.row`, `.col-*`, `.card`, `.nav-tabs` | section links and real runtime status | no fake settings | completed |
| `/settings/models` | Model Provider | Form / Fieldset | `form-layout.html`, `settings.html` | `preview/pages/form-layout.astro`, `preview/pages/settings.astro`, `docs/content/ui/forms/fieldset.mdx` | `.card`, `.card-header`, `.fieldset`, `.form-label`, `.form-control`, `.form-select`, `.alert` | provider fields, capability action | API key stays runtime-only | completed |
| `/settings/prompts` | Prompt Studio | Master-detail / Tabs | `settings.html`, `tabs.html` | `preview/pages/settings.astro`, `preview/pages/tabs.astro` | `.nav-tabs`, `.row`, `.col-*`, `.card`, `.form-control`, `.badge` | prompt data, editor/test events | code editor is textarea | completed |
| `/settings/prompts/:name/versions` | Prompt Versions | Table / Timeline | `tables.html`, `activity.html` | `preview/pages/tables.astro`, `preview/pages/activity.astro` | `.table`, `.table-responsive`, `.activity`, `.badge` | versions, tests, actions | none planned | completed |
| `/settings/prompts/:name/tests` | Prompt Tests | Table / Result detail | `tables.html`, `settings.html` | `preview/pages/tables.astro`, `preview/pages/settings.astro` | `.table`, `.card`, `.alert`, `.badge`, `.form-control` | expected/actual/diff, run status | none planned | completed |
| `/settings/jobs` | AI Jobs | Data table / Logs | `tables.html`, `logs.html` | `preview/pages/tables.astro`, `preview/pages/logs.astro` | `.table`, `.table-responsive`, `.badge`, `.form-select` | jobs, filters, retry | mobile row fallback | completed |
| `/settings/jobs/:id` | AI Job Detail | Detail / Datagrid | `logs.html`, `profile.html` | `preview/pages/logs.astro`, `docs/content/ui/components/datagrid.mdx` | `.page-header`, `.card`, `.datagrid`, `.alert`, `.btn` | job metadata, error, retry | none planned | completed |
| `/settings/memory` | Memory Lifecycle | List / Status | `activity.html`, `settings.html` | `preview/pages/activity.astro`, `docs/content/ui/components/status.mdx` | `.list-group`, `.badge`, `.status`, `.btn` | memory filters/actions | none planned | completed |
| `/settings/memory/:id` | Memory Detail | Datagrid / Timeline | `profile.html`, `activity.html` | `docs/content/ui/components/datagrid.mdx`, `docs/content/ui/components/timeline.mdx` | `.datagrid`, `.activity`, `.badge`, `.list-group` | fact, evidence, history, actions | none planned | completed |
| `/settings/backup` | Backup / Batch | Form / Upload | `form-layout.html`, `dropzone.html` | `preview/pages/form-layout.astro`, `preview/pages/dropzone.astro`, `docs/content/ui/plugins/dropzone.mdx` | `.card`, `.form-control`, `.dropzone`, `.dz-message`, `.alert`, `.btn` | native export/import/reprocess | native input visually wrapped by official pattern | completed |
| `/entries/:id` | Entry Detail | Card / Datagrid | `profile.html`, `markdown.html` | `preview/pages/profile.astro`, `preview/pages/markdown.astro` | `.page-header`, `.card`, `.datagrid`, `.prose`, `.list-group`, `.badge` | raw content, metadata, provenance, actions | markdown integration | completed |
| `/entries/:id/history` | Entry History | Activity / Diff | `activity.html`, `markdown.html` | `preview/pages/activity.astro`, `preview/pages/markdown.astro` | `.activity`, `.card`, `.diff`, `.btn` | versions and diff data | diff text glue | completed |
| `/*` | 404 / Error | Error / Empty | `error-404.html`, `error-500.html` | `preview/pages/error-404.astro`, `preview/pages/error-500.astro` | `.empty`, `.empty-title`, `.empty-subtitle`, `.btn`, `.alert` | message and route action | React route fallback | completed |

## Class fidelity contract

关键页面必须保留以下官方 hierarchy/class family；业务组件只替换内容、数据和事件：

```text
.page
  .navbar.navbar-vertical.navbar-expand-lg
  .navbar.navbar-expand-sm.d-print-none
  .page-wrapper
    .page-header.d-print-none
      .container-xl
        .row.g-2.align-items-center
    .page-body
      .container-xl
        .row.row-deck.row-cards / .card / .list-group / .table / .chat
```

每个组件的最终 class 与源码差异必须同步到本文件或 `TABLER_DEVIATIONS.md`。

## Class fidelity ledger

| Tabler source file | Official class list / DOM | StarMem component | Final class list / difference |
| --- | --- | --- | --- |
| `shared/layouts/DefaultLayout.astro` | `.page` → `.navbar.navbar-vertical.navbar-expand-lg` → `.page-wrapper` → `.page-header.d-print-none` / `.page-body` → `.container-xl` | `AppShell` / `PageFrame` / `PageHeader` | 完全保留；React 只绑定路由、事件和业务 children |
| `shared/components/navbar/Sidebar.astro` | `.container-fluid`, `.navbar-brand.navbar-brand-autodark`, `.navbar-collapse`, `.navbar-nav`, `.nav-item`, `.nav-link`, `.nav-link-icon`, `.nav-link-title`, `.navbar-footer` | `AppShell` / `SidebarGroup` | 完全保留；`a` 按官方 React 事件边界转换为 `button`，class 不变 |
| `shared/components/layout/PageHeader.astro` | `.page-header.d-print-none` → `.container-xl` → `.row.g-2.align-items-center` → `.col` / `.col-auto` / `.page-title` | `PageHeader` | 完全保留；只替换标题、描述和 actions |
| `preview/pages/dropzone.astro` + `docs/content/ui/plugins/dropzone.mdx` | `.dropzone`, `.fallback`, `.dz-message`, `.dropzone-msg-title`, `.dropzone-msg-desc`, `.btn` | Capture / Backup upload | 官方 class 保留；React 绑定既有选择、拖放、列表和 Inbox API |
| `shared/components/cards/SignInCard.astro` + `shared/layouts/SingleLayout.astro` | `.page.page-center`, `.container-tight`, `.card.card-md`, `.card-body`, `.form-label`, `.form-control`, `.btn.btn-primary` | Login | 官方 class 保留；只替换 StarMem 文案与 login handler |
| `docs/content/ui/components/empty.mdx` / `placeholder.mdx` / `status.mdx` | `.empty`, `.empty-bordered`, `.empty-icon`, `.empty-title`, `.empty-subtitle`, `.placeholder-glow`, `.placeholder`, `.status`, `.status-dot` | `EmptyState` / `LoadingState` / `AIStatus` | 官方 class 保留；业务状态映射到 official semantic variant |
| `preview/pages/chat.astro` / `tables.astro` / `settings.astro` / `profile.astro` | `.chat`, `.chat-bubbles`, `.chat-bubble`, `.table`, `.table-responsive`, `.nav.nav-tabs`, `.row`, `.col-*`, `.datagrid`, `.card` | Ask / Jobs / Prompt / Detail workspaces | 使用对应官方组合；StarMem 仅映射真实 API 数据和动作，不新增视觉 primitive |
