## 1. 审计与源码映射（Phase UI-0 / UI-1）

- [x] 1.1 撰写 `docs/ui/UI_AUDIT.md`：现有设计系统、自定义 CSS 清单、页面/组件清单、可复用业务组件、待删除视觉代码
- [x] 1.2 clone 官方 `preline` 仓库到 `.reference/preline` 并记录 commit SHA（`05ca5999…` v5.0.0）
- [x] 1.3 撰写 `docs/ui/PRELINE_SOURCE_MAP.md`：StarMem 页面 → Preline 模板/block/组件源码位置（Timeline/Search/Ask 等随阶段补齐）
- [x] 1.4 将 `.reference/` 加入 `.gitignore`
- [x] 1.5 记录迁移前的功能与测试基线（`pytest` 50 passed、`ruff` 通过、`smoke.sh` passed、`playwright_smoke.py` passed）

## 2. Global Shell（Phase UI-2）

- [x] 2.1 安装 `preline@5.0.0` 并接入 Tailwind v4（`variants.css` + `@source`），构建通过
- [x] 2.2 引入 Preline 设计 tokens（`src/theme/preline-theme.css`），页面背景/字体改用 token
- [x] 2.3 新增 `src/theme/preline.ts` 封装 `HSStaticMethods.autoInit()` 并在页面切换时调用
- [x] 2.4 重构 AppShell：Sidebar、Header、内容 container，复用免费 block 源码 class
- [x] 2.5 移动端 off-canvas（`data-hs-overlay`）+ 底部导航使用 Preline token
- [x] 2.6 暗色模式迁移到 `.dark` + `hs_theme`（`watchTheme()` 跟随系统并支持存储值）
- [x] 2.7 删除旧布局/侧边栏/头部相关 CSS（收口于 Phase UI-6 6.2，`styles.css` 已仅剩功能性样式）

## 3. Capture + Timeline（Phase UI-3）

- [x] 3.1 Capture 改用 Preline composer pattern（plus / dropdown / attachment），移除三枚强视觉 Tab
- [x] 3.2 保存按钮改用 Preline primary action，删除橙色按钮
- [x] 3.3 去掉营销型 eyebrow 与重复标题，主标题改为业务文案
- [x] 3.4 Timeline 改为 Preline 内容流（卡片列表 + Preline 表单筛选）
- [x] 3.5 Entry 卡片精简为时间、内容、少量标签、AI 总状态、`···` 操作
- [x] 3.6 AI Processing 明细移入 `details` 折叠（默认收起）
- [x] 3.7 日期分组改用 Preline divider 视觉，移除饱和日期胶囊
- [x] 3.8 Entry actions 收敛为常驻收藏 + `···` 菜单（复制/固定/编辑/重新处理/删除）

## 4. Search + Ask（Phase UI-4）

- [x] 4.1 Search 使用 Preline searchbox / filter / dropdown / list group，结果标记使用模板 badge
- [x] 4.2 Ask 桌面两栏（会话 / Sources，导航由 AppShell 承担），使用 Preline layout 与表单原语
- [x] 4.3 Sources 移动端使用 Drawer / Bottom sheet（`hidden lg:block` aside + 移动端 bottom sheet，含遮罩、关闭、滚动锁定）
- [x] 4.4 保持来源字段（标题/摘要/时间/Source/片段）与跳转行为不变

## 5. 其余页面（Phase UI-5）

- [x] 5.1 Entry Detail：判定为不适用 —— 详情能力已由 `EntryCard` 的 `expanded` 展开区提供（safety / metadata / tags / entities / related / relations），Phase UI-3 已完成视觉迁移；本仓库无独立详情页面或路由（`openEntry` 仅定位高亮）。用户已确认，记入迁移报告 Deviations
- [x] 5.2 Settings：改为 Preline 表单页模式，移除 Dashboard Card 墙（Provider/AI Jobs 统计卡 + 单一设置容器 `divide-y` 分区）
- [x] 5.3 Prompt Studio：table / form / textarea / select / badge / tabs / dialog 全部使用 Preline 原样式
- [x] 5.4 Login：使用 Preline Auth/Sign-in 模板，仅替换 Logo 与标题
- [x] 5.5 Inbox / Workbench 全量迁移，保持修正、重试、智能视图等业务行为

## 6. 移动与清理（Phase UI-6）

- [ ] 6.1 iOS safe area 实测（Home Indicator、刘海/Dynamic Island、standalone）—— 环境无 iOS 真机/模拟器，仅静态核查，未验证
- [x] 6.2 清理旧视觉 CSS（`styles.css` 325 → 55 行；仅保留 Preline imports、safe-area、color-scheme、reduced-motion）
- [x] 6.3 扫描确认无新 arbitrary value、无硬编码颜色、无第二套视觉体系（硬编码颜色 0、Tailwind 调色板 0；剩余 13 处 arbitrary 均为 Preline 源码语法或 grid 布局必需）
- [x] 6.4 重写 `tests/playwright_smoke.py` selector，覆盖全部页面链路（改为可访问性名称 + 语义锚点；实测 `playwright-smoke: passed`）
- [x] 6.5 产出 1440×1000 / 1920×1080 / 390×844 / 430×932 四尺寸截图并人工检查（由 `starmem-ui-v2-page-architecture` 完成：1440/390/430 截图 + 溢出检查）
- [x] 6.6 生成 `docs/ui/STARMem_PRELINE_MIGRATION_REPORT.md`（Source / Mapping / Removed / Preserved / Mobile / Screenshots / Deviations）—— 由 `docs/ui/STARMEM_UI_V2_COMPLETION.md` 覆盖同等章节
- [x] 6.7 更新 `docs/DEVELOPMENT_STATUS.md` 并运行完整验证（pytest / ruff / smoke / playwright）—— 已完成（2026-09-16）
