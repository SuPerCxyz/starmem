# Design: Preline UI 视觉层重构

## Context

`web/` 是 React 18 + Vite 6 + TypeScript + Tailwind v4，业务逻辑集中在 `src/main.tsx`（1060 行）与 `src/api.ts`。视觉层由 `src/styles.css`（306 行、222 个自定义类）承担，包含硬编码颜色与自建组件语言。

Preline v5 是 Tailwind v4 组件库：交互行为由 headless JS 插件（`dist/*.js`，`hs-*` 前缀与 `data-hs-*` 属性）提供，视觉由 Tailwind utility class 直接写在 markup 中，设计变量由 `theme.css` 的 `@theme` 定义。官方免费分发包含 204 个 blocks、5 个模板、27 个插件；完整 blocks 源码在官网/MCP 提供，本环境无 MCP，因此 SoT 组合使用本地 tokens/模板与官网免费组件 markup。

## Goals / Non-Goals

**Goals**

- 全站视觉唯一来源为 Preline，可直接溯源到具体源码位置。
- 业务功能、API 调用、状态逻辑、交互行为与现有实现等价。
- 桌面与 iOS（390/430）均可用的布局，而非桌面缩放。
- 迁移过程可审计：每页有 Source Mapping，任何偏差逐条记录。

**Non-Goals**

- 不重新设计视觉系统，不新增第二套主题或品牌色。
- 不改后端、schema、API contract、搜索与 Prompt 逻辑。
- 不引入 Preline 之外的 UI 框架或图标库。

## Decisions

### D1. SoT 组合与溯源

- 设计变量：`.reference/preline/theme.css` 与 `css/themes/*`（默认主题 + 字体 token）。
- 结构母版：`.reference/preline/templates/**` 的 5 个免费模板用于 app shell 与页面骨架；`preline.co/docs/components/*` 与 `preline.co/blocks/*` 的免费组件真实 markup 用于区域与叶子组件。
- 每个迁移页面在 `docs/ui/PRELINE_SOURCE_MAP.md` 记录 `StarMem 页面 → Preline 源码 URL/文件 + 使用的 block/component 名称`。
- 找不到对应免费源码时，选择最接近的免费 block，并在迁移报告 `Deviations` 逐条说明；禁止"自行发挥"补齐。

### D2. Preline 集成方式（Tailwind v4）

- 安装 `preline` npm 包（v5），不把 `.reference/preline` 作为 runtime 依赖。
- 在 `src/styles.css` 顶部：

  ```css
  @import "tailwindcss";
  @import "./node_modules/preline/variants.css";
  @source "./node_modules/preline/dist/*.js";
  ```

- 移除现有 `:root` 自建变量（`--surface`/`--brand`/`--accent`/`--radius` 等）与全部自定义组件类，仅保留 `sr-only` 等功能类与 iOS safe area 规则。

### D3. React 与 HS 插件集成

Preline 交互组件是命令式 JS，依赖 DOM 存在后初始化。

- 在 `src/theme/preline.ts` 提供 `initPreline()` 封装 `HSStaticMethods.autoInit()`。
- 在 `App` 容器用 `useEffect` 于路由/页面切换后调用，确保新渲染的 `hs-*` 元素被初始化。
- 不依赖全局销毁；组件卸载由 React 负责，覆盖层通过 Preline 的 `data-hs-overlay` 机制控制。

### D4. 图标体系

- 统一使用 Preline markup 中的内联 SVG（Heroicons 风格，`class="shrink-0 size-4"` + `stroke="currentColor"`）。
- 移除 `lucide-react` 依赖，按语义替换为模板图标；`StarMem` Logo 例外保留。
- 同一页面不得混用多套图标体系。

### D5. 暗色模式

- 采用 Preline 的 `.dark` class + `hs_theme` localStorage 约定，替换现有 `prefers-color-scheme` 变量。
- 所有新增内容必须使用 Preline token class（`bg-white dark:bg-neutral-900` 等），不出现硬编码颜色。

### D6. 组件拆分结构

```
web/src/
  main.tsx              # 应用入口、路由与数据编排
  api.ts                # 不变
  theme/preline.ts      # HS 初始化封装
  components/           # 可复用 Preline 组合（AppShell、Sidebar、Icon 等）
  pages/                # Capture、Timeline、Search、Ask、Settings、PromptStudio、Login、Inbox、Workbench
```

- 只做语法层转换（`class`→`className`、`href`→路由跳转、HTML 事件→React 状态），不改变模板 spacing/radius/typography/surface。
- 业务逻辑与数据获取保持现有实现（`@tanstack/react-query` + `api.ts`）。

### D7. 业务映射要点

- 记录页母版：参考 AI Chat 类布局的居中工作区 + composer；顶部去掉 `YOUR PERSONAL MEMORY REPOSITORY`、`CAPTURE FIRST` 等营销 eyebrow，主标题为「有什么需要记住的？」。
- Capture：使用 composer toolbar / plus button / dropdown / attachment pattern，替代三枚强视觉 Tab；保存按钮使用模板 primary action（蓝色），删除橙色按钮。
- Timeline：使用 timeline / activity feed / list group，去除重 Card dashboard；Entry 只保留时间、内容、少量标签、AI 总状态、`···` 操作；AI 步骤细节默认折叠。
- Search：使用 searchbox、filter、dropdown、list group；结果标记沿用模板 badge。
- Ask：桌面三栏（导航 / 会话 / Sources），移动端 Sources 使用 Drawer/Bottom sheet。
- Prompt Studio / Settings：使用 Application UI 的 table、form、textarea、select、tabs、alert、dialog/drawer。
- Login：使用 Preline Auth / Sign-in 模板，仅替换 Logo 与标题。

### D8. 移动与 iOS

- 桌面左侧 Sidebar；移动端使用 Preline offcanvas/mobile navigation，禁止把桌面 Sidebar 缩成常驻迷你栏。
- 底部导航保留业务五项（记录/时间线/搜索/问记忆/更多），视觉全部取自 Preline token 与组件。
- `padding-bottom: env(safe-area-inset-bottom)`、`padding-top: env(safe-area-inset-top)` 属于允许保留的功能性 CSS，需在 standalone 与 Safari 下实测。

## Risks / Trade-offs

- **回归面广**：222 个类全量重写，涉及 7 个页面与 16 个组件 → 用分阶段实施 + 每阶段功能回归收敛风险。
- **测试失效**：`playwright_smoke.py` 依赖旧 class，重构后必然失败 → 同步重写 selector，禁止以删除断言换取通过。
- **HS 初始化时机**：React 渲染后未初始化会导致交互失灵 → 统一封装并覆盖路由切换路径验证。
- **视觉偏差**：免费 block 与 Pro 母版存在差异 → 记录 Deviation，不自行设计；必要时以免费 block 组合替代。
- **暗色与对比度**：换 token 后需实测 light/dark 可读性。

## Migration Plan

Phase UI-0 审计 → UI-1 源码映射 → UI-2 Global Shell → UI-3 Capture/Timeline → UI-4 Search/Ask → UI-5 其余页面 → UI-6 移动 QA/清理/报告。每阶段完成后运行 `pytest`、`ruff`、`scripts/smoke.sh`、重写后的 `playwright_smoke.py`，并产出 1440/1920/390/430 截图。

## Open Questions

- 无阻塞项。若后续需要 Pro 母版或 MCP，可在此 change 之外追加调整。
