## 1. 审计与骨架（Phase U0）

- [x] 1.1 产出 `docs/ui/STARMEM_UI_V2_AUDIT.md`：当前问题、重复组件、页面角色冲突、旧视觉债务、可复用业务逻辑
- [x] 1.2 建立 OpenSpec change `starmem-ui-v2-page-architecture`（proposal / design / tasks / specs），`openspec validate --strict` 通过
- [x] 1.3 记录改动前基线：构建、`pytest` 50 passed、`ruff` 通过、`smoke.sh` passed、`playwright_smoke.py` passed

## 2. 公共组件（Phase U1）

- [x] 2.1 `PageHeader`（title / description / actions），替换各页自造标题区
- [x] 2.2 `FilterBar`（select / date / scope / count），时间线与搜索页共用
- [x] 2.3 `EmptyState`（title / description / actions / suggestions），覆盖各页空态
- [x] 2.4 `AIStatus`（processing / ready / review / failed + 点击进入详情）
- [x] 2.5 `EntryListItem`（由 `EntryCard` 重构：time / type / tags / content / status / favorite / more）
- [x] 2.6 `SourceItem`（title / time / type / snippet / open），Ask 来源已复用
- [ ] 2.7 `docs/ui/PRELINE_SOURCE_MAP.md` 补充新组件对应的 Preline 来源

## 3. 记录与时间线分离（Phase U2）

- [x] 3.1 记录页改为 Capture-first：`PageHeader` + Composer + 「最近记录 / 查看全部」
- [x] 3.2 记录页新增 `RecentEntries`，限制最近 8 条、无筛选器、独立查询
- [x] 3.3 时间线页接入 `FilterBar`，保留时间范围 / 类型 / 来源 / 计数
- [x] 3.4 日期分组改为分隔线视觉
- [x] 3.5 `EntryListItem` 一级信息收敛：时间 / 类型 / 标签（前 4 个）/ 正文 / 状态 / 收藏 / More
- [x] 3.6 逐项 AI 处理明细移入 AI 详情 Drawer，一级仅显示总状态

## 4. 搜索工作区（Phase U3）

- [x] 4.1 未搜索态：最近搜索（localStorage）+ 保存的搜索 + 知识对象
- [x] 4.2 结果区：结果计数 + 命中类型徽标 + 来源 / 时间 / 片段
- [x] 4.3 空结果态：`EmptyState` + 可操作建议
- [x] 4.4 模式选择使用 Preline select
- [x] 4.5 `SourceItem` 复用于来源展示（Ask）；搜索结果为检索布局

## 5. 问记忆工作区（Phase U4）

- [x] 5.1 未提问态：示例问题 + 最近提问（localStorage）+ `EmptyState`
- [x] 5.2 回答态：对话列（你问 + 答案 + 置信度）+ Sources 一级栏
- [x] 5.3 追问入口：示例 chip，明确标注为新的单轮提问
- [x] 5.4 Sources 可打开原始 Entry；移动端 Bottom Sheet 保留
- [x] 5.5 桌面两栏使用 `lg:grid-cols-[minmax(0,1fr)_20rem]`（无任意宽度数值）

## 6. 移动与一致性（Phase U5 / U6）

- [x] 6.1 390×844 / 430×932 四页 overflow 均为 0；底部导航与 Drawer 无遮挡
- [ ] 6.2 Composer 聚焦、软键盘、真实 iOS Safe Area 实测（本环境无真机，仅静态核查）
- [x] 6.3 Dark Mode 全页检查（`html.dark` 生效，四页深色背景 + 溢出 0，截图 `/tmp/u6-dark-record-1440.png`）
- [x] 6.4 一致性核查：Header / Container / Spacing / Badge / Button / Dropdown / Drawer / Empty State
- [x] 6.5 扫描确认无新增 arbitrary color / radius / shadow / 第二套视觉体系（硬编码颜色 0、Tailwind 调色板 0）
- [x] 6.6 更新 `tests/playwright_smoke.py` 覆盖新结构（AI Drawer、Search 三态、Ask 三态），实测通过
- [x] 6.7 生成验收截图（Desktop 6 张 + Mobile 4 张）
- [x] 6.8 产出 `docs/ui/STARMEM_UI_V2_COMPLETION.md`
- [ ] 6.9 同步 `docs/DEVELOPMENT_STATUS.md` 与 `docs/ui/PRELINE_SOURCE_MAP.md`
- [x] 6.10 完整验证：构建 / `pytest` 50 passed / `ruff` / `smoke.sh` / `playwright_smoke.py`
