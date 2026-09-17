# StarMem 前端 UI 审计（Phase UI-0）

更新时间：2026-09-16
范围：`web/`（React 18 + Vite 6 + TypeScript + Tailwind v4）
关联 change：`openspec/changes/starmem-v2-ui-preline-refactor`

## 1. 技术栈现状

| 项 | 现值 |
| --- | --- |
| 框架 | React 18.3 + react-router-dom 7 |
| 构建 | Vite 6 + `@vitejs/plugin-react` |
| 样式 | Tailwind CSS v4（`@tailwindcss/vite`） |
| 数据 | `@tanstack/react-query` 5 |
| 图标 | `lucide-react` 0.468 |
| 字体 | Atkinson Hyperlegible（在 `styles.css` 内声明） |
| UI 组件库 | 无，全部自建 |

## 2. 设计系统现状（唯一视觉层 = `web/src/styles.css`）

`web/src/styles.css` 共 306 行、**222 个自定义视觉 class**，包含：

- `:root` 自建变量：`--surface`、`--surface-raised`、`--muted`、`--border`、`--brand`(#1e3a8a)、`--brand-strong`、`--accent`(#c2410c)、`--danger`、`--radius`(14px)
- 硬编码颜色：`background:#eff6ff`（整页淡蓝）、`color:#10204a`、focus `#f59e0b`、hover `#9a3412`
- 自建组件语言：`.primary-button`、`.secondary-button`、`.entry-card`、`.source-card`、`.type-chip`、`.day-group`、`.eyebrow` 等

## 3. 页面与组件清单（`web/src/main.tsx`，1060 行）

| 类型 | 名称 |
| --- | --- |
| 页面 | Capture、Timeline、SearchPage、AskPage、InboxPage、WorkbenchPage、MorePage（内含 Settings / Prompt Studio / 数据搬迁） |
| 子组件 | LoginScreen、EntryCard、SearchCard、InboxCard、WorkbenchItems、Workspace、IconButton、App |
| 路由 | `Page = capture \| timeline \| search \| ask \| more \| inbox \| workbench` |

DOM 锚点（重构需保持等价功能）：`.app-shell`、`.sidebar`、`.workspace-header`、`.nav-item`、`.mobile-nav`、`.entry-card`、`.ask-form`、`.scope-form`、`.saved-search-row`、`.source-card`、`.inbox-card`。

## 4. 可复用业务组件（保留逻辑，仅替换视觉）

- 数据层：`web/src/api.ts`（539 行）保持不变
- 状态：react-query 的 query/mutation、草稿存储 `starmem:capture-draft`、focus entry 跳转
- 交互能力：登录、保存、删除、Pin、收藏、编辑、重新处理、Inbox 修正、导出/导入、智能视图

## 5. 待删除的视觉代码

- `styles.css` 中全部自定义视觉 class（222 个）
- 保留：
  - `.sr-only`（无障碍，等价 Tailwind `sr-only` 可替换）
  - iOS safe area 功能性声明（`env(safe-area-inset-*)`）
  - 基础 reset（可由 Tailwind preflight 承担）
- 移除自建 token：`--brand`、`--accent`、`--surface*`、`--radius`、`--danger` 等

## 6. 用户报告问题 → 代码证据

| 用户报告的问题 | 代码证据 |
| --- | --- |
| 整页蓝色背景过重 | `body { background:#eff6ff }`、`--brand:#1e3a8a` |
| 保存按钮橙色不统一 | `.primary-button { background: var(--accent) }` → `#c2410c` / hover `#9a3412` |
| 营销型标题层级过多 | `.eyebrow` + 「YOUR PERSONAL MEMORY REPOSITORY」「CAPTURE FIRST」 |
| 日期胶囊视觉过强 | `.day-group` |
| AI Metadata 默认展开噪声 | `EntryCard` 中 `.entry-ai-steps` / `.entry-metadata` 常驻渲染 |
| 卡片横线/状态/操作过多 | `.entry-footer`、`.entry-actions`、`.entry-meta` 全量常驻 |
| 移动端只是桌面缩小 | 单一布局 + 追加 `.mobile-nav`，无独立移动布局 |

## 7. 受影响的测试与配置

- `tests/playwright_smoke.py` 依赖上述旧 class，重构后必须重写 selector
- `web/index.html`：`theme-color:#1e3a8a`、标题含营销文案
- `web/Dockerfile`：`npm install` + `npm run build`（无 lockfile）

## 8. 外部参考现状

- `.reference/preline`：官方仓库 clone，commit `05ca59998db345cfede649b00093032409b37f25`（v5.0.0）
- `.reference/preline-blocks/centered-ai-chat-workspace.html`：从官网免费 block 提取的真实 markup（133,420 字符）
- 本环境无 Preline MCP，完整 blocks 通过官网免费页面获取
