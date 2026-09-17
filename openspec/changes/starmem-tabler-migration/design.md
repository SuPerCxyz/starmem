## Context

当前 Web 入口由 Tailwind v4、Preline CSS/JS、Preline theme token 和本地 SVG wrapper 共同控制；页面逻辑集中在 `web/src/main.tsx`，Shell 在 `web/src/components/AppShell.tsx`，共享视觉 primitive 在 `web/src/components/ui.tsx`。官方 Tabler 已在 `.reference/tabler` 的 commit `0776b88863690c9740d7d33988a8b5df66aad6dc` 成功安装并构建，生成 `core/dist` 与可运行 preview。

## Goals / Non-Goals

**Goals:**

- 让生产 Web 只加载锁定的 Tabler CSS/JS 与 Tabler Icons，并使用官方 `page/navbar/page-wrapper/page-header/page-body/container-xl/row/col/card/list-group/form-control/form-select/table/chat/empty/status` DOM/class。
- 在不改变 API、后端、数据与原有用户链路的前提下迁移全部 Inventory 页面。
- 保存官方 Demo 参考截图与每个 StarMem Route 的源码映射、class fidelity、checksum 和 deviation 证据。
- 用 Bootstrap/Tabler responsive classes 取代 Tailwind 视觉布局；保留可访问性、PWA、safe-area 和必要业务交互 glue。

**Non-Goals:**

- 不新增业务功能、API、数据库字段、Worker 行为或第三方 connector。
- 不修改 Tabler vendor CSS；不引入另一套 UI kit，也不通过新 CSS 重新设计 Tabler。
- 不把 Tabler Pro-only block 当作可免费复制的来源；没有直接对应页面时只组合 pinned commit 中真实存在的官方页面/组件。

## Decisions

### 1. Vendor 官方构建产物，而不是重新编译主题

从 `.reference/tabler/core/dist` 复制官方 `tabler.css`/`tabler.min.css`、`tabler.esm.js`/`tabler.esm.min.js` 与 `tabler-theme.esm.js`/min 及其必要 map/字体资产到 `web/src/vendor/tabler/`，生产入口导入复制后的只读文件。这样 CSS 的字节内容能由 commit、官方 `pnpm run build` 和 checksum 复现。

替代方案：直接依赖 npm `@tabler/core` 会让 UI 随 lockfile/registry 解析漂移；仅引用 CDN 无法保证离线 Compose 运行；自行重写 SCSS 会违反唯一源码约束。

### 2. React 使用官方 Tabler Icons React 包

以 pinned Tabler build 使用的 Icons 版本为基准，安装 `@tabler/icons-react@3.46.0`，在 `web/src/components/icons.tsx` 仅做语义别名导出，保留业务调用方但让输出来自官方 `Icon*` 组件。移除 `lucide-react` 与旧手写/Preline icon wrapper。

替代方案：继续手写 `<svg>` 会无法证明图标来自官方包；把 Tabler SVG 全部内嵌到业务文件会增加重复代码和审计成本。

### 3. 先迁移共享外壳与 primitive，再逐页替换 class

`AppShell` 输出 Tabler 官方 vertical navbar layout：`.page`、`.navbar.navbar-vertical.navbar-expand-lg`、`.navbar-brand`、`.navbar-nav`、`.navbar-footer`、水平 `.navbar.navbar-expand-sm`、`.page-wrapper`、`.page-header`、`.page-body` 和 `.container-xl`。`ui.tsx` 保留业务语义组件，但其输出只使用来自官方页面/组件的 class。页面组件继续复用现有 API hooks 和状态逻辑，按六类母版排列 Tabler `row`/`col-*`。

替代方案：在 Tailwind 上覆盖 Tabler class 会产生 cascade 双系统；只改颜色/圆角而保留旧结构不能满足 DOM fidelity。

### 4. 使用 Tabler data attributes 与官方 JS 做交互

生产入口加载官方 `tabler.esm.js`，主题入口加载 `tabler-theme.esm.js`，主题状态改用 Tabler `data-bs-theme`、`tabler-theme` localStorage 与官方默认配置。Dropdown、collapse、offcanvas、modal 使用 `data-bs-*` markup；React 仅负责状态数据和在挂载/路由变化后让官方插件初始化。

替代方案：继续保留 `hs-*`/Preline JS 会违反视觉系统唯一性；自写 Drawer/Dropdown 状态虽然能工作，但会重复官方交互并造成 DOM 漂移。

### 5. CSS 只保留最小集成 glue

删除 Tailwind import、Preline variants/theme 及页面视觉 CSS。`web/src/styles.css` 仅保留 Tabler vendor import、safe-area、PWA/浏览器兼容、功能性 overflow 和 reduced-motion；每一条新规则写入 `docs/ui/TABLER_DEVIATIONS.md`。

### 6. 以 Route Inventory 和真实数据驱动验证

扩展 Playwright route matrix，覆盖静态与动态嵌套页面、390/430/768/1024/1440/1920、light/dark、console/pageerror、horizontal overflow、上传/过滤/详情/返回/重试等路径。截图同时保存 Tabler reference 和 StarMem output；不使用假 KPI 或假 Source。

## Risks / Trade-offs

- [Bootstrap/Tabler class 与旧 Tailwind class 大量不同] → 先保留业务组件接口，逐页替换 class 并以官方源码行号做 mapping；构建失败时按页面分阶段修复。
- [Tabler CSS 体积大于当前按需 Tailwind bundle] → 接受官方完整 CSS 作为唯一 vendor 资产；不为了体积重写或裁剪 CSS，后续如需拆分必须基于 Tabler 官方构建入口并重新记录 checksum。
- [官方最新 commit 只声明 Safari 17.5+ 等浏览器支持] → 保留现有 PWA/safe-area 逻辑，Playwright 覆盖移动视口，并把真实 iOS Safari/Home Screen 作为明确未验证项。
- [React 重新渲染可能让 Bootstrap data API 状态与 DOM 暂时不同步] → 使用官方 ESM JS、稳定 id/data-bs-target、路由变更后初始化；核心业务操作仍由 React handler 控制并做交互回归。
- [部分 StarMem 业务没有 Tabler 同名成品页] → 使用 pinned preview/docs 中实际存在的最近 component/page，并在 source map/deviations 记录业务重排而不改视觉属性。

## Migration Plan

1. 记录 Tabler commit/version/clone time，运行官方 build，保存 `preview/pages` 参考截图，复制 vendor 资产并记录 checksum。
2. 更新 OpenSpec 与 Route Inventory，锁定 Tabler source mapping 和允许的 deviation。
3. 替换依赖与 CSS/JS 入口，迁移 `icons.tsx`、Shell、共享 primitive 和主题初始化。
4. 按 Capture/Browse/Search/AI/Detail/Management/Auth/Error 顺序逐页迁移，保留现有 API 与业务状态。
5. 更新 smoke/traversal/composition 测试与截图，执行 Web/API/Playwright/Tabler build 及 CSS/Preline/Tailwind/inline style audit。
6. 失败回滚策略是恢复 StarMem 前端入口、组件和 package lock；`.reference/tabler`、docs 证据与 vendor 文件作为迁移记录保留，不回滚后端数据。

## Open Questions

无。Tabler commit、vendor 路径、图标版本和迁移边界已由当前请求与官方源码确定。
