# P1 Gap Closure 实现与验证

更新时间：2026-09-15
OpenSpec change：`starmem-v2-p1-gap-closure`

## 范围

补齐 P0/已确认 P1 范围内的真实缺口：Relation 读取、AI Metadata 人工编辑、Project/Topic/Entity 管理、Inbox 手工修正、图片描述降级、批量重处理与全库重建、Reranker、Ask 查询日志与「最近常问」、性能基线及 OpenSpec 生命周期收尾。外部 Connector、CLI/MCP、浏览器插件、P2 高级能力不在本次范围。

## 后端

- `GET /api/v1/entries/{id}/relations`：出边/入边、目标 Entry 摘要、类型、置信度、来源；Entry 不存在返回 404。
- `GET/PATCH /api/v1/entries/{id}/metadata`：类型、Summary、Project、Topic、Importance；Summary/Project/Topic 写 `is_user_locked` 观测，AI 重跑跳过；Importance 限制 0–100；未知 Project/Topic 返回 404/422；清空锁定值会删除用户观测。
- Project/Topic/Entity：重命名、合并、排除、恢复；合并把源对象观测重指向目标并把源标记 `merged`，排除只改状态，不删 Entry/观测；默认列表仅显示 `active`。
- `PATCH /api/v1/inbox/{job_id}`：修正标题与内容类型，追加 `EntryVersion`，附件与 provenance 不变；处理中 409，未知任务 404。
- `ImageDescriptionProvider`：默认关闭；无附件直接 `skipped`，无 Provider 记 `skipped` + `image_description_disabled`，异常记 `failed`；Entry metadata 读取接口返回描述、状态与降级原因。
- `POST /api/v1/entries/reprocess-batch`：显式 ID 或过滤器，上限 200；超限/不存在 ID 返回 422 且不创建任务；返回 submitted/failed 计数。
- `POST /api/v1/maintenance/rebuild-embeddings`：排队全库 Embedding 重建，不复制或删除原文。
- Reranker：默认 `none`；HTTP Rerank 成功按分数重排并记录 `search.rerank` 指标，异常或返回数量不匹配回退原 Hybrid 排序。
- Ask 日志：`ask_queries` 记录脱敏查询、source_scope、结果计数与耗时，不保存答案正文；「最近常问」聚合最近 30 天高频脱敏查询。

## Web

- Entry 详情：相关记录（方向、类型、置信度、跳转、空态、错误态）、图片描述与降级提示、Metadata 编辑面板（类型、Importance、Summary、Project、Topic、锁定标识、标签、实体）。
- Inbox：修正标题/内容类型的表单与成功/失败反馈。
- Workbench：重命名、合并、排除、恢复入口；默认隐藏 merged/excluded。
- More：批量重处理（二次确认、submitted/failed 反馈）与全库 Embedding 重建。

## 验证记录

```text
docker compose exec -T api pytest -q
# 37 passed, 7 warnings

docker compose exec -T api ruff check app tests alembic
# All checks passed!

docker compose exec -T api ruff format --check app tests alembic
# 63 files already formatted

scripts/smoke.sh
# integration-smoke: passed

docker compose build web
# built

STARMEM_TEST_EMAIL=admin@starmem.local STARMEM_TEST_PASSWORD=change-this-password python3 tests/playwright_smoke.py
# playwright-smoke: passed

openspec validate --all --strict
# 23 passed, 0 failed（本 change 归档并同步主 spec 后）
```

新增后端测试 `backend/tests/test_p1_gap_closure.py`（8 项）覆盖：关系读取/空态/404、Metadata 锁定与重跑不覆盖、非法值、Workbench 合并/排除不删证据、Inbox 修正与 409/404、批量上限与计数、图片描述降级、Reranker 成功/失败/数量不匹配回退、Ask 脱敏聚合与 Smart View。

Playwright 真实链路新增：相关记录、Metadata 保存反馈、Inbox 修正、批量入口存在性、「最近常问」聚合。

## 未验证与限制

- 真实图片描述 Provider 的成功路径需外部 vision 模型凭据，本环境未配置，只验证了降级路径。
- Reranker 成功路径使用 mock HTTP 响应，未连接真实 Reranker 服务。
- 真机 iOS/Android 分享、Web Push、Passkey 等仍属后置范围，未在本次实施。
- 100k Entry / 500k Chunk 性能目标受本机资源限制，实测规模与降级见 `docs/P0_COMPLETION_REPORT.md` 的 Performance 章节。

## OpenSpec 生命周期

- 本次归档 5 个既有 change：`starmem-v2-p0`、`starmem-v2-p1-ingestion`、`starmem-v2-p1-knowledge-workbench`、`starmem-v2-p1-mobile-share`、`starmem-v2-p1-portability`，delta 已同步到 `openspec/specs/`。
- `starmem-v2-p1-gap-closure` 在实现与验证完成后归档。
