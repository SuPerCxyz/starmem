# 统一 StarMem 页面母版与信息架构

## Why

`starmem-v2-ui-preline-refactor` 已完成视觉层向 Preline 的迁移，但仍存在结构性问题：

- 四个主页面（记录 / 时间线 / 搜索 / 问记忆）共用同一骨架——「标题 + 输入框 + 列表或空白」，用户无法一眼区分页面角色。
- 搜索页与问记忆页在未操作状态下几乎整页空白，不像完整产品。
- 时间线 Entry 卡片默认铺开 AI Pipeline 明细（Embedding / 分类 / 标签 / 实体 / Memory / Relation / Job 状态），噪声高。
- 记录页与时间线页内容重复，未体现「快速记录」与「按时间浏览」的角色差异。
- 各页 Header、Filter、Empty State、Badge、Action 排布各自为政。

本次不改视觉体系，只重新组织**页面骨架、信息密度与业务结构**。

## What Changes

- **新增 6 个公共组件**（外观全部复用 Preline）：`PageHeader`、`FilterBar`、`EmptyState`、`AIStatus`、`EntryListItem`、`SourceItem`。
- **记录页**收敛为 Capture-first：Capture Composer + 最近 8 条 + 「查看全部」入口，不再内嵌完整时间线。
- **时间线页**成为完整历史浏览器：统一 `FilterBar`（时间范围 / 类型 / 来源 / 计数）+ 日期分组 divider + 完整分页。
- **搜索页**补齐三态：未搜索态（保存的搜索、知识对象、最近记录）、结果区（命中类型 Badge、来源、时间）、空结果态（可操作的改进建议）。
- **问记忆页**补齐三态：未提问态（示例问题、最近提问）、回答态（对话列 + Sources 一级栏 + 追问入口）、来源 Bottom Sheet。
- **AI 处理明细二级化**：Entry 一级视图只保留状态徽标，点击打开 Drawer 查看完整 per-step 处理明细与重试。
- **状态语义统一**：处理中 / 已整理 / 需复核 / 失败（`processing` / `ready` / `review` / `failed`）。
- **Entry More 菜单**接入既有 `GET /entries/{id}/versions` 的「查看历史」（只读 diff，不含 restore）。

## Impact

- Affected specs:
  - `ui-page-architecture`（新增）
  - `ui-parity-closure`（修改：Entry 逐项 AI 状态由一级常显改为二级 Drawer）
- Affected code:
  - `web/src/main.tsx`（页面重组）
  - `web/src/components/`（新增公共组件）
  - `web/src/lib/recent-activity.ts`（新增：localStorage 最近搜索 / 最近提问）
  - `tests/playwright_smoke.py`（同步 selector）
- 不改后端 schema 与 API；仅接入既有端点（versions / ai-status / saved-searches / entities / projects / topics / reviews）。
- 不做：多轮 AI 会话上下文、AI 生成追问建议、统计/KPI 卡片、任何视觉 token 变更。
