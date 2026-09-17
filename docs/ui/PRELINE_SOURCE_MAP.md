# Preline Source Map（已废弃，仅历史记录）

StarMem 已在 2026-09-16 完成 Tabler 严格模板迁移。本文件仅保留为历史交接索引，不再是当前 UI Source of Truth；请使用 [`TABLER_SOURCE_MAP.md`](TABLER_SOURCE_MAP.md)、[`TABLER_VENDOR_INFO.md`](TABLER_VENDOR_INFO.md) 和 [`STARMEM_TABLER_MIGRATION_REPORT.md`](STARMEM_TABLER_MIGRATION_REPORT.md)。当前前端不再加载 Preline CSS、JS 或 `hs-*` UI class。

## Source of Truth

| 项 | 值 |
| --- | --- |
| 仓库 | `https://github.com/htmlstreamofficial/preline.git` |
| commit | `05ca59998db345cfede649b00093032409b37f25` |
| 版本 | v5.0.0（2026-08-21） |
| 本地路径 | `.reference/preline`（仅开发参考，已加入 `.gitignore`） |
| npm 依赖 | `preline@^5.0.0` |
| 设计 tokens | `.reference/preline/theme.css` → 复制为 `web/src/theme/preline-theme.css` |
| 插件变体 | `node_modules/preline/variants.css` |
| 交互插件 | `node_modules/preline/dist/*.js`（`HSStaticMethods.autoInit()`） |
| License | MIT + Preline UI Fair Use（免费模板可商用） |

### 免费 block 提取

本环境无 Preline MCP，免费 block 的真实 markup 从其官网公开页面提取：

| block | 来源 URL | 本地缓存 |
| --- | --- | --- |
| Centered AI Chat Workspace with Prompt Suggestions | `https://preline.co/blocks/communication/ai-chat-layouts/` | `.reference/preline-blocks/centered-ai-chat-workspace.html` |

提取到的关键事实：上游路径为 `blocks/communication/ai-chat-layouts/iframes/free/centered-ai-chat-workspace-with-prompt-suggestions...`，即该 block 属于**免费**集合；同分类下 `threaded-ai-chat-workspace...` 位于 `iframes/pro/`，不使用。

## 页面映射

| StarMem 页面/区域 | Preline 来源 | 说明 |
| --- | --- | --- |
| App Shell（侧边栏 + 主区 + 顶栏） | `centered-ai-chat-workspace.html` 的 `#hs-pro-sidebar` + `<main class="md:ps-65 ...">` + `<header class="... bg-navbar ...">` | class 原样复用 |
| 侧边导航项 | 同 block `<a class="group relative w-full flex items-center gap-1 py-1.5 px-2.5 ... before:...">` | `before:` 伪元素作为 active 指示条 |
| 移动端导航 | Preline `hs-overlay`（`data-hs-overlay="#starmem-sidebar"`） | 桌面侧栏在移动端变为 off-canvas |
| 底部移动导航 | Preline token（`bg-navbar` / `border-sidebar-line` / `text-primary`） | 业务五项，无现成 block，仅用 token 组合 |
| Capture Composer | 同 block 的 composer：`bg-layer border border-line-3 rounded-2xl shadow-xs` + `<textarea data-hs-textarea-auto-height>` + `<div class="hs-dropdown">`（＋ 添加内容） | 替代旧三 Tab |
| Composer 工具下拉 | 同 block 的 `hs-dropdown` 菜单项 class（`text-dropdown-item-foreground hover:bg-dropdown-item-hover`） | |
| Timeline / 最近记录 | `centered-ai-chat-workspace.html:557-700` 的主区布局；Preline list/divider token | 日期 Feed、Filter scope、compact list |
| Search | `src/plugins/combobox/README.md:100-165`、`centered-ai-chat-workspace.html` 的 workspace shell、Preline list/divider token | Filter disclosure、recent/saved/results/no-result |
| Ask + Sources | `centered-ai-chat-workspace.html:557-884`、Preline list-group/badge/offcanvas token | Conversation、Sources rail/Drawer、prompt suggestions |
| Entry Detail | `src/plugins/overlay/README.md:60-112`、Preline card/list/sidebar token | Raw main、Metadata/Provenance rail、History |
| Settings | `templates/dashboards/cms-admin/index.html:69-120`、Preline form/alert/tabs token | ManagementNav、form sections、status feedback |
| Prompt Studio | `templates/dashboards/cms-admin/index.html:69-120`、`src/plugins/datatable/README.md`、Preline tabs/select token | Prompt list/editor、version table、test result detail |
| Login | Preline auth form/button/token composition；本地 pinned tree 无可直接复用的免费 Auth block | 仅替换 Logo、StarMem 文案和认证字段 |

## 设计 tokens 使用约定

- 颜色/圆角/字体一律使用 `theme.css` 定义的语义 token：`bg-background`、`bg-sidebar`、`text-foreground`、`text-muted-foreground-1`、`border-sidebar-line`、`bg-navbar`、`text-primary`、`bg-layer`、`bg-dropdown` 等。
- 暗色：`.dark` class（`@custom-variant dark (&:where(.dark, .dark *))`）。
- 图标：Preline markup 使用的 24×24、`stroke-width:2`、`currentColor` 内联 SVG，集中在 `web/src/components/icons.tsx`。
- 禁止新增任意值（`[13px]`）、硬编码颜色与自建视觉类。

## 全站 Page Composition Mapping（2026-09-16）

| 页面母版 | StarMem 页面/表面 | 固定 Preline 参考 | 实施映射 |
| --- | --- | --- | --- |
| Capture Workspace | `/capture`、文件/图片导入 | `.reference/preline-blocks/centered-ai-chat-workspace.html:714-884`；`src/plugins/file-upload/README.md:115-160` | Composer、`data-hs-textarea-auto-height`、上传 Dropzone 结构、Recent Feed |
| Browse Workspace | `/timeline`、`/inbox`、`/workbench`、`/sources` | `centered-ai-chat-workspace.html:51-220`；`templates/dashboards/cms-admin/index.html:69-120` | grouped filters、divider/list、master-detail、真实 provenance |
| Search Workspace | `/search`、Saved Search | `src/plugins/combobox/README.md:100-165`；search/list tokens | Search header、filter disclosure、recent/saved/results/no-result |
| AI Workspace | `/ask`、Ask Sources | `centered-ai-chat-workspace.html:557-884` | conversation column、prompt suggestions、Sources rail/Drawer |
| Detail Workspace | `/entries/:id`、history、Workbench detail、Memory/Job detail、Prompt version | `src/plugins/overlay/README.md:60-112`；Preline list/divider/card tokens | main content + metadata/provenance rail；mobile stacked/Drawer |
| Management Workspace | `/settings*`、Prompt editor/history/tests、AI Jobs、Memory、Backup | `templates/dashboards/cms-admin/index.html:69-120`；`src/plugins/datatable/README.md` | ManagementNav、table/list、form sections、action/status feedback |

## Deviations

- 固定 commit 的本地 Preline 仓库没有可直接复用的免费 Auth Page block；Login 使用其 form/button/token 组合，并保留这一 deviation。
- 固定 commit 没有 Source Management/Connector Sync 数据 contract；`/sources` 只从真实 Entry provenance 派生浏览，明确不展示虚构同步状态。
- 固定 commit 的 File Upload plugin 依赖 Dropzone；StarMem 继续使用原生 `input[type=file]` 作为可访问/兼容选择器，并将其视觉入口做成 Preline Dropzone composition，不新增 Dropzone 依赖或改变上传 API。
- Entry/Memory/AI Job/Prompt 详情没有一套直接的免费业务 block；使用 overlay、list、table 和 dashboard 的最近 Composition，并在页面 Inventory 中逐项记录。
