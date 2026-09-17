## Why

StarMem 当前的页面视觉由 Preline、Tailwind utility 和 Lucide 组合而成，导致同一业务在不同页面使用不同的 DOM、密度和状态表达。用户已明确将 Tabler 官方仓库、官方 Demo 和官方构建产物设为唯一视觉事实源，因此需要把前端从“参考模板”迁移为可追溯的 Tabler DOM/class 实现。

## What Changes

- **BREAKING** 将 Web 视觉系统从 Preline 迁移到锁定 commit 的 Tabler/Bootstrap 官方 CSS、JS 和 Tabler Icons。
- 克隆并构建 `.reference/tabler`，保存官方 Demo 参考截图、commit/version、构建命令、vendor 文件 checksum 与源码映射。
- 扫描并覆盖全部 StarMem 用户可访问 Route、嵌套详情、设置子页、认证、错误页和由面板触发的逻辑页面。
- 将 Application Shell、Sidebar、Header、Capture、Browse、Search、AI、Detail、Management、Auth/Error 逐页改为 Tabler 官方页面/组件 DOM 与 class 的 React 化实现。
- 移除迁移页面的 Preline 依赖、`hs-*` 结构、Lucide 图标和 Tailwind 视觉控制；仅保留必要的业务 glue 与 iOS/PWA 功能 CSS，并记录每项 deviation。
- 保留现有 API contract、数据模型、AI/Worker、上传、搜索、问记忆、编辑、删除、收藏、Inbox、Workbench、Prompt、Jobs 与 Memory 行为。
- 补充 Tabler 迁移 Inventory、Source Map、Vendor Info、Deviation、参考/产物截图和最终迁移报告。

## Capabilities

### New Capabilities

<!-- No new business capability; this is a visual-system and page-composition migration. -->

### Modified Capabilities

- `ui-design-system`: 将唯一视觉源、CSS/JS、图标、主题、响应式和自定义 CSS 约束从 Preline 改为锁定版本的 Tabler 官方源码与构建产物。
- `ui-page-architecture`: 保留六类 StarMem 页面母版，但要求每个 Route 的页面结构映射到真实 Tabler layout/component DOM/class，并覆盖所有状态与视口。

## Impact

- 前端：`web/src`、`web/package.json`、Vite/CSS 入口、页面组件、路由、图标与测试选择器。
- Vendor：`web/public/vendor/tabler/`（或等价只读路径）中的官方构建 CSS/JS/字体/必要图标资产，来源为 `.reference/tabler/core/dist`。
- 文档与证据：`docs/ui/`、Tabler 参考截图、页面 Inventory、Source Map、Vendor Info、Deviations 和迁移报告。
- 验证：Tabler 官方构建、StarMem Web/API 构建、Playwright 全路由/移动/暗色/console/overflow QA；不修改后端核心逻辑或 API contract。
