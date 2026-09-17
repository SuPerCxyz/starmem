# P1 设计文档对齐闭环（parity-closure）实施记录

> 对应 OpenSpec change：`openspec/changes/starmem-v2-parity-closure`（归档后为 `openspec/changes/archive/2026-09-16-starmem-v2-parity-closure`）。
> 目标：补齐设计文档中 P0 与已确认 P1 范围内缺失的用户可见行为，使日常使用路径完整闭环。

## 1. 范围

- Capture 支持 Ctrl/Cmd+Enter 保存与空内容提示，保留按钮路径。
- Entry 卡片直接展示标签与逐项 AI 状态（索引/Embedding/分类/摘要/标签/实体/时间/项目/主题/Memory/关系/图片描述），失败项可重试。
- 一条 Entry 多分类 `content_types`，保留 `content_type` 主分类与向后兼容读取。
- Related Entry 确定性信号：共享实体、共享标签、同 Project、同 Topic、同 Error、同 Host、语义相似度，并返回命中理由。
- 时间线自定义起止日期，保留今天/昨天/本周/本月预设。
- 搜索全文/语义/混合模式与类型/标签/实体/项目/主题/时间过滤；Saved Search 保存并复用完整过滤器。
- Memory 生命周期：确认、标记 expired、删除、状态筛选。
- Prompt Studio：克隆内置 Prompt、编辑 Layer 2 Task Prompt 与模型参数、Preview、Draft 测试、用户自定义 Test Case CRUD。

明确排除：CLI、MCP、浏览器插件、External Connector、第三方导入、离线/推送/相机/语音/Passkey、P2 能力。

## 2. 后端实现

### 2.1 数据与迁移

- `backend/alembic/versions/0010_parity_closure.py`：新增 `entries.content_types JSONB NOT NULL DEFAULT '[]'` 与 `memories.expired_at TIMESTAMPTZ`。
- `backend/app/models.py`：`Entry.content_types` 使用 PostgreSQL `JSONB`（使 `@>` 包含查询有效）；`Memory.expired_at`。
- 读取回退：`EntryOut` 的 `model_validator` 在 `content_types` 为空时回填 `[content_type]`，不需要数据回填迁移。

### 2.2 API 与服务

- `backend/app/api.py`
  - `GET /entries/{id}/related`：返回 `RelatedEntryOut`（`score` + `reasons`）。
  - `GET /entries/{id}/ai-status`：返回 `EntryAIStatusOut`（逐项 job_id/label/status/error）。
  - `POST /memories/{id}/expire`：写入 `expired` 状态与 `expired_at`/`valid_to`。
  - `POST /prompts/{name}/clone`：把内置 Prompt 克隆为可编辑 Draft。
  - `GET/POST/PATCH/DELETE /prompts/{name}/test-cases`：用户自定义 Test Case CRUD；内置用例拒绝修改与删除（409）。
  - 列表与详情 Entry 响应批量附带 `tags` 与 `ai_status_items`，避免每卡片 N+1 请求触发限流。
- `backend/app/services/curation.py`：`entry_signal_map`（批量标签与逐项 job）、`entry_ai_status_items`、`entry_ai_status`；多分类人工编辑与用户锁定沿用既有 Observation 机制。
- `backend/app/services/related.py`：确定性信号计算与理由聚合。
- `backend/app/services/search.py`：模式与类型/标签/实体/项目/主题/时间过滤；`content_types` 与主分类同时命中。
- `backend/app/prompting.py`：`create_draft` 支持 Task Prompt 与 provider/model/temperature/top_p/max_tokens；`clone_builtin_draft`。
- `backend/app/memory_engine.py`：`expire_memory`。

### 2.3 关键交互

- `content_types` 为空时读取返回主分类集合；用户编辑后写入 `classification` Observation 锁定，AI 重跑不覆盖。
- `EntryOut.tags` / `EntryOut.ai_status_items` 由 `list_entries`、`read_entry` 批量填充；失败任务复用既有 `/ai-jobs/{id}/retry`。
- 未配置 Chat Provider 时，Chat 依赖步骤（摘要/项目/主题/Memory/关系）标记为 `skipped` + `provider_not_configured`，而非 `failed`；`skipped` 计入 `ready` 聚合，卡片显示“已跳过（未配置）”。配置 Chat 后重新处理即可执行。真正配置了但请求失败的仍为 `failed` 并可重试。`image_describe` 对非图片 Entry 记为 `skipped`，卡片显示“已跳过”。

## 3. 前端实现

- `web/src/main.tsx`
  - Capture：文本输入 `Ctrl/Cmd+Enter` 保存，空内容显示提示。
  - EntryCard：类型 chips、标签 chips、逐项 AI 状态（失败项重试）、多分类编辑、Related 命中理由。
  - Timeline：自定义起止日期与预设联动。
  - SearchPage：模式选择、高级过滤器（类型/标签/实体/项目/主题/日期）、Saved Search 还原过滤器。
  - MorePage：Memory 状态筛选与确认/标记过期/删除；Prompt Studio 克隆、Task Prompt 与模型参数编辑、Preview、Draft 测试结果、Test Case 增删。
- `web/src/api.ts`：对应类型与请求封装；`search` 支持模式与过滤器；`draftPrompt` 支持完整参数。
- `web/src/styles.css`：标签、AI 步骤、日期过滤、过滤器网格、测试结果、Test Case 编辑等样式；`.timeline-tools` 允许换行以保持窄屏无横向溢出。

## 4. 测试

### 4.1 后端

- `backend/tests/test_parity_closure.py`：多分类写入/检索/回退、Related 确定性理由、AI 状态聚合、Memory 过期/筛选/删除、Prompt 克隆/参数/Test Case CRUD、Saved Search 过滤器复用、克隆不影响 Production。

### 4.2 端到端

- `tests/playwright_traversal.py`：逐页面执行关键按钮并断言状态变化与业务效果（Capture 键盘保存、Entry 卡片标签/逐项状态/多分类、时间线日期范围、搜索模式与 Saved Search 过滤器还原、Memory 生命周期、Prompt Studio 克隆/参数/预览/Test Case）。测试自清理其 Entry、Memory、Saved Search、Prompt Draft 与自定义 Test Case。
- `tests/playwright_smoke.py`：更新“相关记录”断言为精确匹配，适配新增加载文案。

说明：完整遍历测试请求量高于默认 `STARMEM_RATE_LIMIT_PER_MINUTE=120`，验证时通过临时 Compose override 将限流调高后运行，验证后已恢复默认值；产品默认限流未修改。

## 4.3 页面执行错误排查与修复

对全部页面逐项执行交互并收集 console error / pageerror / HTTP>=400 后修复：

- Workbench 切换 Project/Topic/Entity 标签时，`kind` 立即变化而 `selectedId` 仍为上一个类型的 ID，导致 `GET /projects/{topic|entity id}` 返回 404。修复：切换标签时同步清空 `selectedId`，并让详情查询仅在 `selectedId` 属于当前类型列表时启用。
- 移除 Entry 卡片的逐卡片 `tags`/`ai-status` 请求，改为列表批量返回，消除由此引发的 429 与页面错误。
- `tests/playwright_smoke.py` 现在会删除自己创建的 Inbox 修正 Entry，避免测试残留。

## 5. 验证结果

```text
docker compose exec -T api pytest -q
45 passed, 8 warnings

docker compose exec -T api ruff check app tests alembic
All checks passed!

docker compose exec -T api ruff format --check app tests alembic
66 files already formatted

docker compose build web
TypeScript/Vite build passed

scripts/smoke.sh
integration-smoke: passed

python3 tests/playwright_smoke.py
playwright-smoke: passed

python3 tests/playwright_traversal.py
playwright-traversal: passed

openspec validate --all --strict
24 passed, 0 failed
```

## 6. 限制

- AI 状态展示依赖已创建的 AI Job；Chat 未配置时 Chat 类任务显示失败并可重试，不影响原文。
- Related 信号为有界多次查询，候选数量受限，不保证穷举。
- Prompt Studio 允许编辑 Layer 2 Task Prompt 与模型参数；系统安全契约与 Output Schema 仍只读。
