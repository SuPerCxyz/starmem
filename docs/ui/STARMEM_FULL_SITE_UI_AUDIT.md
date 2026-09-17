# StarMem 全站 UI Composition Audit（Tabler 严格迁移）

## 审计范围

- Route/逻辑页面：23 个，来源为 `web/src/lib/routes.ts`、`main.tsx`、Shell、设置子页、详情与可独立验证的 offcanvas。
- 视觉唯一源：Tabler 官方仓库 `https://github.com/tabler/tabler.git`，commit `0776b88863690c9740d7d33988a8b5df66aad6dc`，version `1.5.1`。
- 官方 Preview 已实际启动并构建，参考截图位于 `docs/ui/reference/tabler/`。
- 业务边界：只迁移前端 DOM/class/CSS/Icons/interaction wiring，不修改 API、数据库、Memory Engine、Search Engine、Prompt Engine 或 Worker。

## 页面分类

| 母版 | Route / surface | Tabler 官方基线 | 迁移重点 |
| --- | --- | --- | --- |
| A Capture Workspace | `/capture`、文件/图片导入 | `layout-vertical`、`form-layout`、`dropzone` | page-header + card/form/input-group + recent list |
| B Browse Workspace | `/timeline`、`/inbox`、`/workbench`、`/sources` | `activity`、`email-inbox`、`layout-vertical` | activity/list/table/master-detail |
| C Search Workspace | `/search`、Saved Search | `search-results`、list-group/table | search controls + results/no-result |
| D AI Workspace | `/ask`、`/ask/sources` | `chat`、chat component、offcanvas | chat bubbles + Sources list/offcanvas |
| E Detail Workspace | Entry/Memory/Job/Workbench/Prompt versions | `profile`、`markdown`、`activity`、datagrid | raw/main + metadata/history/provenance |
| F Management Workspace | `/settings*`、Prompt、Jobs、Memory、Backup | `settings`、`form-layout`、`tables`、`logs` | settings nav + form/table/detail |

## 当前问题与目标

| 领域 | 迁移前问题 | Tabler 目标 |
| --- | --- | --- |
| Shell | Preline `hs-*` + Tailwind 自定义布局 | 官方 `.page` / vertical navbar / `.page-wrapper` / `.page-header` / `.page-body` / `.container-xl` |
| 视觉 token | Preline theme + arbitrary utility + local SVG wrapper | 官方 `tabler.css` semantic variables/classes + official Icons |
| 页面 Composition | 多页局部拼装、详情停留在 Drawer | 官方 page/component DOM 直接 React 化，详情具备 datagrid/list/timeline |
| 响应式 | 桌面布局压缩，组件自制移动 Drawer | 官方 Bootstrap/Tabler breakpoint、offcanvas、responsive table/list |
| 状态 | 各页自定义空/加载/错误样式 | 官方 `empty`、`placeholder/spinner`、`alert`、`status/badge` |

## 优先级

1. T0 Inventory 与 Tabler source/build evidence
2. T1 vendor CSS/JS、官方 Icons、主题与 Shell
3. T2 Capture、Timeline、Inbox、Workbench、Sources
4. T3 Search、Ask、Sources
5. T4 Entry、Memory、Entity/Topic/Project、History
6. T5 Settings、Models、Prompt Studio、Prompt Tests、AI Jobs、Backup
7. T6 Login、404/Error
8. T7 Mobile、PWA safe area、Dark Mode、overflow、console
9. T8 cleanup、class fidelity、最终报告

## 状态结论

详细逐页状态见 [`STARMEM_PAGE_INVENTORY.md`](STARMEM_PAGE_INVENTORY.md)。23 个逻辑页面表面均已完成 Tabler DOM/class、四态、桌面/移动/暗色和业务回归，Inventory 与 [`TABLER_SOURCE_MAP.md`](TABLER_SOURCE_MAP.md) 当前全部标记为 `completed`。

## 结论

审计基线、官方源码/Demo 构建、页面迁移、截图、状态和最终验证均已完成；已知限制与唯一既有格式检查失败记录在 [`STARMEM_TABLER_MIGRATION_REPORT.md`](STARMEM_TABLER_MIGRATION_REPORT.md)。
