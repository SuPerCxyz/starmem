## Why

StarMem 已有完整的核心业务能力，但前端页面仍以单个组件拼接为主：管理功能集中在一张长页、详情停留在局部 Drawer、宽屏利用率不一致，导致不同入口的任务结构和完成度不统一。现在需要把现有逻辑页面一次性收敛到可复用的 Preline 页面母版，并为后续页面建立明确的 Composition 约束。

## What Changes

- 枚举 `/` 下所有逻辑页面、管理子页面、详情面板、加载/空/错误状态，并建立可持续维护的页面 Inventory 与全站审计报告。
- 将现有页面归入 Capture、Browse、Search、AI、Detail、Management 六类母版，统一 Page Header、内容容器、状态呈现、列表/Feed、详情 Rail/Drawer 和移动布局。
- 将 More 长页拆为管理导航与独立的 Settings、Model/Provider、Prompt Studio、Prompt History、Prompt Tests、AI Jobs、Memory、Backup/Import 工作区；继续复用现有 API，不制造假数据。
- 完善 Entry、Memory、Project、Topic、Entity、AI Job 等已有数据入口的详情 Composition，并为已有业务状态提供 Empty、Loading、Error、Loaded 反馈。
- 保持 Raw-first、现有 API contract、数据模型、AI 处理边界和核心交互不变；不引入第二套设计系统或新的后端业务能力。
- 固定并记录官方 Preline reference commit，更新 StarMem → Preline source map 与未来页面 Composition 规则。

## Capabilities

### New Capabilities

- `ui-composition`: 定义 StarMem 全站 Route/逻辑页面的六类页面母版、完整状态、真实数据和未来页面约束。

### Modified Capabilities

无。现有 `ui-design-system` 与 `mobile-pwa` 的视觉和基础响应式要求继续适用；本 change 新增页面级 Composition 约束并覆盖其未表达的全站完整度要求。

## Impact

- 主要改动 `web/src/main.tsx`、`web/src/components/AppShell.tsx`、`web/src/components/ui.tsx`、`web/src/api.ts` 及新增/拆分的页面组件。
- 更新 `docs/ui/PRELINE_SOURCE_MAP.md`、新增 `docs/ui/STARMEM_PAGE_INVENTORY.md`、`STARMEM_FULL_SITE_UI_AUDIT.md`、`UI_COMPOSITION_RULES.md` 和最终 Composition 报告。
- 可能补充已有后端只读详情接口的前端 client 调用；不修改数据库、Worker、搜索算法、Prompt Engine 或公共 API contract。
- 使用已有 Preline 依赖和 `.reference/preline` 作为参考，不新增 UI 依赖。
