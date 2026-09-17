## Why

当前 Web 视觉层是自建的一套 CSS：`web/src/styles.css` 306 行、222 个自定义类，写死 `#eff6ff` 页面背景、`#1e3a8a` 品牌色与 `#c2410c` 橙色主按钮；`web/src/main.tsx` 1060 行单文件同时承载全部页面结构与视觉。它直接导致用户确认的问题：整页蓝色过重、主按钮与全站不统一、营销型 eyebrow 层级过多、Capture 与 Timeline 割裂、Entry 卡片信息噪声大、移动端只是桌面缩小版。

用户要求以 Preline UI 官方模板为**唯一视觉来源**重构前端视觉层，而不是"参考后自行设计"。已确认边界：以免费资源作为 Source of Truth、图标统一替换为模板内联 SVG、`main.tsx` 拆分组件、分阶段实施。

当前环境事实：Preline 官方仓库已 clone 到 `.reference/preline`，commit `05ca59998db345cfede649b00093032409b37f25`（v5.0）；`Centered AI Chat Workspace with Prompt Suggestions` 不在免费仓库，本环境亦无 Preline MCP，因此 SoT 由本地 `theme.css`/`css/themes/*`/5 个免费模板与 `preline.co/docs`、`preline.co/blocks` 免费组件的真实 markup 组成。

## What Changes

- 引入 Preline UI v5（npm `preline`）及其设计 tokens（`.reference/preline/theme.css`、`css/themes/*`），移除自建 CSS 变量与组件类。
- 删除 `styles.css` 中全部自定义视觉类，仅保留 iOS safe area 等功能性 CSS。
- 将 `web/src/main.tsx` 拆分为 `pages/` + `components/`，视觉结构直接复用 Preline 源码 markup 与 class，不做二次设计。
- 图标体系从 `lucide-react` 全量替换为 Preline 模板使用的内联 SVG。
- 暗色模式迁移到 Preline 的 `.dark` + `hs_theme` 体系，保持现有明暗行为。
- 按页迁移：Global Shell → Capture/Timeline → Search/Ask → Entry Detail/Settings/Prompt Studio/Login/Inbox/Workbench。
- 同步重写 `tests/playwright_smoke.py` 的 selector，并新增 1440/1920/390/430 四尺寸截图验收。
- 产出 `docs/ui/UI_AUDIT.md`、`docs/ui/PRELINE_SOURCE_MAP.md`、`docs/ui/STARMem_PRELINE_MIGRATION_REPORT.md`。

非目标：不改后端、API contract、schema、搜索算法、Memory/Prompt 逻辑与 Worker；不引入 Tailwind/Preline 之外的 CSS 框架（禁 shadcn/MUI/AntD/Bootstrap）；不做营销 Hero、KPI Dashboard、渐变、玻璃拟态或装饰插画。

## Capabilities

### New Capabilities

- `ui-design-system`: 约束 Web 视觉层唯一使用 Preline UI 源码结构与 class，禁止自建视觉语言、Tailwind arbitrary value 与硬编码颜色，并定义分阶段迁移、四尺寸截图验收与 Deviation 记录要求。

### Modified Capabilities

（无。`ui-parity-closure`、`mobile-pwa` 等既有行为契约保持不变，本次只替换视觉实现，不改变交互行为与 API 响应。）

## Impact

- 前端：`web/package.json`（新增 `preline`）、`web/src/styles.css`（重写）、`web/src/main.tsx`（拆分）、新增 `web/src/pages/*`、`web/src/components/*`、`web/src/theme/*`。
- 测试：`tests/playwright_smoke.py`（selector 重写）；四尺寸截图脚本。
- 文档：新增 `docs/ui/*`；更新 `docs/DEVELOPMENT_STATUS.md`。
- 参考：`.reference/preline`（commit `05ca599…`）仅作开发参考，加入 `.gitignore`，不进入交付。
- 无后端、数据库、API 变更；现有业务功能与 API 行为保持兼容。
