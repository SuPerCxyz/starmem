## Why

StarMem 已切换到 Tabler，但当前只继承了官方系统字体栈，尚未明确处理中文 glyph fallback，也没有自动证明实际渲染字体与官方 Demo 一致。字体观感和 Typography Fidelity 需要从主观检查升级为可重复的浏览器/CDP/截图验收。

## What Changes

- 读取并锁定 pinned Tabler commit 的真实 typography tokens、font stack、feature settings、字号和行高。
- 在不改变 Tabler 字号、字重、行高、字距和组件结构的前提下，补充明确且全站一致的 CJK fallback。
- 新增隐藏的 Tabler typography fixture route，使用官方 DOM/class 覆盖导航、正文、控件、Badge、Status、Table、Code 等样本。
- 新增自动化 typography validation：自动检查 Reference/StarMem 可用性，启动缺失的本地服务，执行 Computed Style、CDP Rendered Fonts、Bounding Box、PNG diff、font network 和 console/pageerror 审计。
- 新增真实页面 typography audit，覆盖 Capture、Timeline、Search、Ask、Settings 的 light/dark 与四个固定 viewport。
- 记录审计、产物、偏差、阈值和最终报告；不修改业务 API、数据库、Worker 或既有页面 Composition。

## Capabilities

### New Capabilities

- `ui-typography-validation`: 为 Tabler 页面建立确定性的字体 Fixture、浏览器字体校验和截图回归能力。

### Modified Capabilities

- `ui-design-system`: 将 Tabler typography、CJK fallback、实际 rendered font 和 typography regression 纳入唯一视觉系统约束。

## Impact

- 前端：`web/src/styles.css`、内部 fixture route/component、npm scripts。
- 测试工具：`scripts/ui/validate-tabler-typography.mjs`、`scripts/ui/audit-page-typography.mjs` 及最小图像/CDP 依赖。
- 文档：`docs/ui/TABLER_TYPOGRAPHY_AUDIT.md`、`docs/ui/TABLER_DEVIATIONS.md`、`docs/ui/STARMEM_TABLER_TYPOGRAPHY_REPORT.md`。
- 运行时服务：仅在校验时按环境变量启动/探测官方 Tabler Preview 与 StarMem；不改变生产服务配置或业务接口。
