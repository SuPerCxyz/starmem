# 设计决策

## Context

- 视觉唯一来源：Preline UI（`.reference/preline` v5.0.0 + `src/theme/preline-theme.css`）。
  本次不新增任何视觉 token、字体、颜色、圆角、阴影。
- 前端为单文件 `web/src/main.tsx`（约 1670 行），页面按 `Page` 联合类型切换。
- 后端提供 `GET /entries/{id}/versions` 与 `/versions/{n}/diff`、`GET /entries/{id}/ai-status`，
  但 UI 未接入。

## Goals / Non-Goals

**Goals**：让四个主页面角色分明、信息密度合理、空状态完整；统一公共组件与状态语义。

**Non-Goals**：后端多轮会话、AI 生成的追问建议、统计类模块、视觉体系调整。

## Decisions

### D1. Ask 保持单轮（Q1A）

后端 `POST /ask` 无会话状态，不返回建议。因此本次实现**对话式布局**（问题 → 答案 → Sources → 追问入口），
但追问等同于发起新提问，不保留会话上下文、不做多轮记忆。
理由：避免跨层改造；后端能力未就绪时造会话是假功能。

### D2. 最近搜索 / 最近提问使用 localStorage（Q2A）

新增 `web/src/lib/recent-activity.ts`，在本地记录用户真实操作（搜索词、提问词），最多各 6 条。
理由：单用户自托管场景下这是真实行为数据，且无需后端变更；不产生伪造内容。

### D3. 知识对象复用既有全量 API（Q3A）

搜索页未搜索态展示「保存的搜索」（`/saved-searches`）与「知识对象」（`/projects`、`/topics`、`/entities`），
文案标注为「知识对象」而非「最近使用」，避免语义失真。

### D4. AI 明细使用 Drawer 而非 Modal

理由：Entry 详情内容长、需要保留列表上下文；移动端 Drawer 复用既有 Bottom Sheet 模式
（`hidden lg:block` + 移动端 fixed 面板），与 Sources Drawer 保持一致。

### D5. 记录页与时间线页共用组件、不共用数据流

提取 `EntryListItem` 作为唯一渲染单元；记录页使用不带筛选、限制 8 条的查询参数，
时间线页保留完整筛选与无限滚动。避免在同一组件内用 `mode` 分支隐式分叉。

### D6. 状态映射

| 一级展示 | 来源 `ai_status` |
|---|---|
| 处理中 | `pending` / `retrying` |
| 已整理 | `done` / 空（已索引） |
| 需复核 | `partial` |
| 失败 | `failed` |

逐项 `ai_status_items` 仅在 Drawer 展示。

### D7. 与既有 spec 的冲突处理

`ui-parity-closure` 的「Entry 逐项 AI 处理状态」要求卡片展示逐项状态并提供重试。
本次以 MODIFIED 形式收敛为：**一级只显示总状态，逐项明细与重试移入 AI 状态 Drawer**。
重试入口能力不删除，只改变位置。

## Risks / Trade-offs

| 风险 | 处理 |
|---|---|
| 记录页/时间线页拆分可能影响分页与筛选行为 | 记录页独立查询参数，时间线页保持原逻辑；两页分别回归 |
| AI 明细移入 Drawer 改变既有交互路径 | 同步更新 `tests/playwright_smoke.py` 断言 |
| localStorage 记录在不同设备不同步 | 单用户场景可接受；文档中标注为已知限制 |
| `main.tsx` 持续膨胀 | 公共组件拆到 `web/src/components/` |

## Migration

无数据迁移。旧 `styles.css` 已在上一 change 清理，本次不新增自定义 CSS。
