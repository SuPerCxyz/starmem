# StarMem UI Composition Rules（Tabler）

## 唯一视觉来源

StarMem Web 唯一视觉 Source of Truth 是锁定 commit 的 Tabler 官方源码、官方 Preview、官方 CSS/JS 构建产物和 Tabler Icons。页面必须先选 Tabler 官方 page/layout/component，再绑定 StarMem 业务数据；不得参考截图自行猜字体、颜色、间距、圆角、阴影或组件。

官方基线见 [`TABLER_SOURCE_MAP.md`](TABLER_SOURCE_MAP.md) 与 [`TABLER_VENDOR_INFO.md`](TABLER_VENDOR_INFO.md)。vendor 文件是只读上游资产，升级必须显式更新 commit、build、checksum 和 mapping。

## 六类页面母版

StarMem 页面必须归入且只归入一种业务母版，但视觉结构来自 Tabler 官方 Composition：

1. Capture Workspace：Tabler `page-header` + `card` + `form-control`/`input-group`/`btn` + recent list/dropzone。
2. Browse Workspace：Tabler `activity`/`timeline`/`list-group`/`table` + filters/master-detail。
3. Search Workspace：Tabler search-results/list/table/empty。
4. AI Workspace：Tabler chat/chat-bubbles/chat-bubble + Sources list/offcanvas。
5. Detail Workspace：Tabler card/datagrid/list-group/tabs/timeline/markdown。
6. Management Workspace：Tabler settings/form/fieldset/table/datagrid/status/alert。

禁止把所有页面实现为“标题 + 一张自定义 Card + 一个 Form”，也禁止用同一个窄单列容器覆盖所有任务。

## React 化边界

允许：

- `class` → `className`、`for` → `htmlFor`、官方 Tabler DOM 转 JSX。
- 用真实 API 数据替换 Demo 文案/行/头像/状态。
- 用 React props、事件、条件渲染和 route Link 保留业务行为。
- 用官方 `data-bs-toggle` / `data-bs-target` / `offcanvas` / `collapse` / `dropdown` markup，并在 React commit 后初始化官方 Tabler JS。

禁止：

- 修改 Tabler vendor CSS/JS。
- 引入 Preline、Lucide、第二套组件库或新的 Tailwind visual utility。
- 自建 `.starmem-card`、`.pretty-input`、`.timeline-box` 等视觉类。
- arbitrary value、视觉 inline style、hard-coded color、私有字体/字号/圆角/阴影。
- 为了“更好看”改变官方 class 的 size、spacing、radius、shadow、container 或 breakpoint。

## Shell 与共享组件

所有用户页面必须经过统一 Tabler Shell：`.page`、`.navbar.navbar-vertical`、`.navbar-nav`、`.navbar-footer`、`.page-wrapper`、`.page-header`、`.page-body`、`.container-xl`。共享组件输出必须来自已记录的 Tabler Source Mapping：

- `PageHeader`
- `FilterBar`
- `EmptyState`
- `LoadingState`
- `ErrorState`
- `AIStatus`
- `EntryListItem`
- `SearchResultItem`
- `SourceItem`
- `FileUploadPanel`
- `MetadataPanel`
- `DetailRail`
- `ManagementNav`

## 状态完整性

每个 Route 必须可核对 Empty、Loading、Error、Loaded；加载使用 Tabler `placeholder`/`spinner`，错误使用 `alert`/`empty`，状态使用 `status`/`badge`。页面不得通过假 KPI、假 Source、假图表或假同步状态填充空间。

## 响应式与 PWA

优先使用 Tabler/Bootstrap `row`、`col-*`、responsive table/list、navbar/offcanvas/collapse。必须检查 390×844、430×932、768、1024、1440×1000、1920×1080；不得横向溢出。`safe-area-inset-*` 仅作为 PWA 功能 glue，必须记录在 [`TABLER_DEVIATIONS.md`](TABLER_DEVIATIONS.md)。

## 新页面门禁

新增 Route 前必须：

1. 在 `STARMEM_PAGE_INVENTORY.md` 登记 Route、母版、状态和 Tabler source。
2. 从 pinned Tabler 源码选择真实 page/component，并记录 source file、DOM sections、原始 class 与 StarMem class。
3. 复用既有 StarMem 页面母版和 shared composition，不创建第二套 primitive。
4. 通过 light/dark、mobile/desktop、focus/touch、console/pageerror、overflow 和业务链路检查后才能标记 `completed`。
