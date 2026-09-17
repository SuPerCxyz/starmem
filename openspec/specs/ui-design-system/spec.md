# ui-design-system Specification

## Purpose
让 StarMem 的 Web 视觉层唯一由 Preline UI 官方源码承载：结构、交互组件与设计 token 直接复用上游，禁止自建视觉语言、任意值与硬编码颜色；同时保证既有业务功能、API 行为与移动端体验不回退。
## Requirements
### Requirement: 视觉来源唯一性

所有 Web 界面结构 SHALL 复用 Preline UI 官方源码（免费模板、免费 block、免费组件 markup）的 class 与 DOM 结构，并 SHALL 在 `docs/ui/PRELINE_SOURCE_MAP.md` 中可溯源。

#### Scenario: 页面可溯源
- **WHEN** 迁移完成一个页面
- **THEN** 该页面在 `PRELINE_SOURCE_MAP.md` 中存在对应 Preline 模板/block/组件源码位置记录

#### Scenario: 无对应免费源码
- **WHEN** 目标页面在 Preline 免费资源中不存在直接对应实现
- **THEN** 使用最接近的免费 block/组件替代，并在迁移报告 `Deviations` 中逐条说明，不得自行设计

### Requirement: 禁止自建视觉与任意值

前端代码 SHALL NOT 新增自建视觉 CSS 类、Tailwind arbitrary value（尺寸/圆角/阴影/颜色）或硬编码颜色，`theme.css` token 与 Preline class 除外。

#### Scenario: 代码扫描
- **WHEN** 对 `web/src` 执行硬编码颜色与 arbitrary value 扫描
- **THEN** 不存在本次新增的 `#xxxxxx`、`[13px]`、`shadow-[...]` 等自建视觉值

#### Scenario: 功能性 CSS 例外
- **WHEN** 需要 iOS safe area 等浏览器兼容规则
- **THEN** 允许保留该功能性 CSS，且不得用于承担视觉样式

### Requirement: 图标体系统一

全站图标 SHALL 使用 Preline 模板中的内联 SVG；SHALL NOT 混用多个图标库或 emoji 充当图标。

#### Scenario: 替换完成
- **WHEN** 迁移完成
- **THEN** `lucide-react` 依赖已移除，页面图标均来自模板内联 SVG，仅 StarMem Logo 例外

### Requirement: 暗色模式

界面 SHALL 沿用 Preline 的 `.dark` 与 `hs_theme` 机制，并在浅色与深色下保持可读对比。

#### Scenario: 切换主题
- **WHEN** 用户在界面切换明暗模式
- **THEN** 全站背景、文本、边框、交互状态使用对应 token 且无不可读区域

### Requirement: 业务功能不回退

视觉层重构 SHALL NOT 改变既有业务行为与 API 契约，包括创建 Entry、Timeline 过滤、Markdown/代码渲染、AI 状态、编辑、删除、Pin、收藏、搜索、问记忆、来源引用、Inbox 修正、Workbench、登录与设置。

#### Scenario: 功能对照
- **WHEN** 迁移完成
- **THEN** 重写后的端到端测试覆盖上述链路且全部通过，API 请求路径与请求体保持不变

### Requirement: 移动端独立布局

移动端 SHALL 使用 Preline 的 off-canvas / mobile navigation / Drawer 模式，而不是将桌面布局等比缩小。

#### Scenario: iPhone 视口
- **WHEN** 在 390px 与 430px 视口打开各页面
- **THEN** 无横向溢出，导航与 Sources/元数据通过 Drawer 呈现，safe area 不遮挡底部导航

### Requirement: 分阶段验收

迁移 SHALL 按 Global Shell → Capture/Timeline → Search/Ask → 其余页面 → 移动 QA 的顺序推进，每个阶段 SHALL 通过功能回归与四尺寸截图检查后方可进入下一阶段。

#### Scenario: 阶段完成
- **WHEN** 某阶段声明完成
- **THEN** 已通过 `pytest`、`ruff`、`scripts/smoke.sh`、重写后的 `playwright_smoke.py`，并产出 1440×1000 / 1920×1080 / 390×844 / 430×932 截图

