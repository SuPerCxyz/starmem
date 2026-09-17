# 未完成功能补齐：任务与进度清单

> 本文件是本次「补齐全部未完成功能」的进度事实源。每完成一项就更新状态。
> OpenSpec change：`starmem-v2-p1-gap-closure`（已归档至 `openspec/changes/archive/2026-09-15-starmem-v2-p1-gap-closure/`）。
> 状态：`[ ]` 未开始 · `[~]` 进行中 · `[x]` 已完成 · `[!]` 阻塞或需裁决
> 批次 1 已全部完成并归档；批次 2/3 是用户已确认后置的跨层能力，未获新的 Requirement Review 确认前不实施。

更新时间：2026-09-15
最终验证：`pytest 37 passed` · `ruff check/format` 通过 · `smoke` 通过 · `web build` 通过 · `Playwright` 通过 · `openspec validate --all --strict` 23/23 通过 · 基准脚本实跑 2,000 Entry。

---

# 批次 1 · 已完成范围内的真实缺口（已完成）

> 收尾说明：批次 1 全部完成并归档。批次 2/3 属于用户已确认后置的跨层能力，未实施，需新的 Requirement Review 与确认。

## 1.1 基础设施 —— 已完成

- [x] 建立 OpenSpec change `starmem-v2-p1-gap-closure`，`openspec validate --strict` 通过
- [x] Alembic migration `0009_p1_gap_closure`：`ask_queries` 表、`projects/topics/entities.status`、`projects/topics.metadata_json`、`prompt_versions.schema_json`
- [x] 模型扩展：`AskQuery`、`Project/Topic/Entity.status`、`Project/Topic.metadata_json`、`PromptVersion.schema_json`
- [x] 配置项：`reranker_provider/base_url/model/timeout_seconds`、`image_description_enabled/base_url/model/timeout_seconds`（默认关闭）

## 1.2 Relations（相关记录）

- [x] `backend/app/services/relations.py`：出边/入边、目标 Entry 摘要、置信度、方向
- [x] Schema：`RelationOut` / `RelationTargetOut`
- [x] `GET /api/v1/entries/{entry_id}/relations`
- [x] 前端 Entry 详情「相关记录」区块（跳转目标、空态、错误态）
- [x] 测试：有关系 / 无关系 / Entry 不存在

## 1.3 AI Metadata 人工编辑

- [x] `backend/app/services/curation.py`：summary/project/topic 用户观测 upsert、content_type/importance 更新
- [x] Schema：`EntryMetadataInput` / `EntryMetadataOut`
- [x] `GET /api/v1/entries/{entry_id}/metadata`
- [x] `PATCH /api/v1/entries/{entry_id}/metadata`
- [x] `ai_tasks.py`：AI 重跑跳过 `is_user_locked` 观测、`user_confirmed` 标签、`user` 来源实体
- [x] 前端 Metadata 编辑面板（标签、类型、项目、Topic、Summary、Entity、Importance、锁定标识）
- [x] 测试：人工修改后重跑不被覆盖、非法值 422、清空锁定值

## 1.4 Project / Topic / Entity 管理

- [x] `curation.py`：`rename_object` / `merge_object` / `set_object_status` / `merge_entity`
- [x] API：`PATCH /projects/{id}`、`POST /projects/{id}/merge`、`POST /projects/{id}/exclude`、`/restore`
- [x] API：`PATCH /topics/{id}`、`POST /topics/{id}/merge`、`POST /topics/{id}/exclude`、`/restore`
- [x] API：`PATCH /entities/{id}`、`POST /entities/{id}/merge`、`/exclude`、`/restore`
- [x] `workbench.py` 列表与 Smart View 默认隐藏 `merged` / `excluded` 对象
- [x] 前端 Workbench 管理入口（重命名、合并、排除、恢复）
- [x] 测试：合并迁移观测、排除不删证据、重命名冲突 409、实体合并入口

## 1.5 Inbox 手工修正

- [x] `PATCH /api/v1/inbox/{job_id}`：修正标题与内容类型，追加 `EntryVersion`，附件与 provenance 不变
- [x] 处理中返回 409；未知任务 404
- [x] 前端 Inbox 修正表单与反馈
- [x] 测试

## 1.6 图片描述

- [x] `ImageDescriptionProvider` + OpenAI-compatible vision 实现（默认关闭，无 Key 不可用）
- [x] `image_describe` Job 类型 + Worker `_run_image_description_job`
- [x] 无附件 → `skipped`；无 Provider → `skipped` + 原因；异常 → `failed`
- [x] `entry.ai_status` 聚合接受 `done` 与 `skipped`
- [x] 前端 Entry 展开显示图片描述与降级原因
- [x] 测试：Provider 可用（Mock）/ 不可用 / 非图片 Entry

## 1.7 批量重处理与全库重建

- [x] `backend/app/services/batch.py`：`reprocess_batch`（ID 列表或过滤器，上限 200）、`rebuild_embeddings`
- [x] Schema：`BatchReprocessInput/Out`、`MaintenanceOut`
- [x] `POST /api/v1/entries/reprocess-batch`
- [x] `POST /api/v1/maintenance/rebuild-embeddings`
- [x] 前端 More / Workbench 批量入口（二次确认 + submitted/failed 反馈）
- [x] 测试：超限 422、空过滤、不存在的 ID、提交计数

## 1.8 Reranker

- [x] `backend/app/services/reranking.py`：HTTP Rerank、索引对齐、指标、失败回退原序
- [x] 接入 `services/search.py` Hybrid 结果
- [x] 测试：启用成功重排、失败回退原序、返回数量不匹配回退

## 1.9 Ask 查询日志与「最近常问」

- [x] `backend/app/services/analytics.py`：`record_query`（`redact_secrets` + 截断）、`frequent_queries` 聚合
- [x] `ask.py` 调用 `record_query`（含 latency、result_count）
- [x] `ask-frequent` 加入 `SMART_VIEW_DEFINITIONS` 并在 `run_smart_view` 实现分支
- [x] 测试：脱敏落库、空数据、聚合排序、窗口边界

## 1.10 性能基线与收尾

- [x] `scripts/benchmark.py`：Raw 保存 / FTS / Hybrid / Ask 本地检索，P50/P95 + JSON 输出
- [x] 实际运行并记录真实数字（2,000 Entry / 200 chunk；100k/500k 降级已记录）
- [x] 回填 P0 完成标准清单；P0 报告补 `Performance` 章节
- [x] README / DEVELOPMENT_STATUS / phase 文档更新
- [x] Playwright 覆盖：相关记录、Metadata 编辑、Inbox 修正、批量操作、「最近常问」
- [x] 全量验证：37 passed、ruff check/format 通过、smoke 通过、web build 通过、Playwright 通过
- [x] archive 既有 5 个 change 并同步主 spec；本 change 已在验证通过后 archive

---

# 批次 2 · P1 后置能力（尚未开始）

## 2.1 CLI

- [ ] `starmem add "..."` / `dmesg | starmem add --type log`
- [ ] `starmem search <query>` / `starmem ask "<question>"` / `starmem get <id>`
- [ ] `console_scripts` 入口、Token 认证（`STARMEM_API_TOKEN`）、超时与错误码
- [ ] 测试：参数解析、stdin 管道、API 错误映射

## 2.2 MCP Server

- [ ] 工具：`starmem_search`、`starmem_get`、`starmem_add`、`starmem_ask`、`starmem_find_related`、`starmem_get_entity`、`starmem_get_project`
- [ ] stdio / SSE 传输、Token 鉴权、结果条数上限、错误脱敏
- [ ] 测试：每个工具的成功与错误路径

## 2.3 浏览器插件（MV3）

- [ ] Save to Memory：保存网页、选中文字、网页+注释、截图、链接
- [ ] 右键菜单 + popup、当前页正文提取、CSRF/Token 复用既有 API
- [ ] 不落盘凭据；测试：fixture 页面、离线/未登录提示

## 2.4 External Corpus Connector 框架

- [ ] Adapter 注册表与配置界面（`Source.config_json`）
- [ ] `discover → fetch → normalize → persist → ContentUnit → FTS → Embedding` 异步流水线
- [ ] 增量同步：`sync_cursor`、`last_synced_at`、幂等、失败重试
- [ ] `GET/POST /api/v1/sources`、Connector 触发与状态查询
- [ ] 至少一个参考实现（本地目录或 RSS），其余保持适配器接口
- [ ] 测试：幂等、cursor 恢复、外部只读边界

## 2.5 第三方导入

- [ ] Memos、Obsidian、Trilium、Notion、Karakeep、ChatGPT、Claude、Markdown 文件夹
- [ ] ZIP 导入（含附件解包）与导入预览/去重报告
- [ ] 每类适配器 fixture 测试；未知格式明确拒绝

## 2.6 Prompt Studio 高级模式

- [ ] 克隆内置 Prompt 并完整编辑 Layer 2（Task Prompt）
- [ ] Schema 高级模式 + 高风险警告（`prompt_versions.schema_json` 已预留列）
- [ ] 模型参数版本化可在 UI 编辑（temperature/top_p/max_tokens/model/provider）
- [ ] 用户自定义 Test Case CRUD（表已存在，缺 API/UI）
- [ ] Draft vs Production 对比视图（复用 diff/test 接口）
- [ ] 默认 Prompt 升级检测与「查看差异 / 合并更新 / 保持当前」

## 2.7 移动端 P1

- [ ] 离线查看最近记录（Cache Storage/IndexedDB + 只读回退）
- [ ] 离线新建 Entry + 恢复网络后同步（队列、冲突处理、幂等）
- [ ] Web Push（VAPID、订阅管理、权限提示）
- [ ] App Badge
- [ ] 相机拍照记录（`capture="environment"` + 直接入库）
- [ ] 语音快速记录（MediaRecorder + 转写，模型不可用时降级为附件）
- [ ] Passkey / Face ID（WebAuthn，模型/环境不可用时标注未验证）

---

# 批次 3 · P2 高级能力（尚未开始）

- [ ] Knowledge Graph UI（次要视图）
- [ ] Relation Graph（Entry ↔ Entity ↔ Topic ↔ Memory）
- [ ] Topic Evolution（时间维度的主题演化）
- [ ] Project Evolution
- [ ] Advanced Memory Consolidation（跨 Entry 长文知识整合；当前仅有 Hook）
- [ ] 自动知识归并（Knowledge 去重与合并）
- [ ] 主动提醒旧知识
- [ ] Agent 主动读取 Memory（供外部 Agent 调用的上下文接口）
- [ ] 多数据源同步
- [ ] 邮件导入
- [ ] IM 导入
- [ ] GitHub Issue / PR 导入
- [ ] Calendar Event 导入
- [ ] 自动每日总结
- [ ] 自动每周总结
- [ ] Memory Quality Score
- [ ] Knowledge Gap Detection
- [ ] Long-term Trend Analysis
- [ ] Personal Knowledge Synthesis

---

# 明确排除（用户已确认）

- 多人 / RBAC：与单用户自托管定位冲突，本次不实施
- 原「明确不做」：复杂目录树、强制标题、保存前选分类/项目、复杂块编辑器、协同编辑、评论、Kanban、Calendar 管理、AI 自动修改原文、Graph 作为主 UI、纯向量搜索、完全依赖 LLM、自动删除历史 Memory
- 技术排除：Elasticsearch/OpenSearch、Kubernetes、微服务拆分

---

# 真实环境限制（不得表述为已验证）

- 真机 iOS/Android：Home Screen 安装、系统分享菜单、键盘、网络切换、Safe Area、Face ID
- 邮件 / IM / GitHub / Calendar / 外部 Connector 的真实连通性（需账号与环境）
- 视觉与语音模型：可插拔 + 无模型降级，不强制本机下载大模型
- 性能 100k Entry / 500k Chunk 目标受本机资源限制，达不到时记录实际规模与降级原因

---

# 验证命令（仓库门禁）

```bash
docker compose up -d --build
curl http://localhost:18000/health
docker compose exec -T api pytest -q
docker compose exec -T api ruff check app tests alembic
docker compose exec -T api ruff format --check app tests alembic
docker compose build web
scripts/smoke.sh
STARMEM_TEST_EMAIL=admin@starmem.local \
STARMEM_TEST_PASSWORD=change-this-password \
python3 tests/playwright_smoke.py
openspec validate starmem-v2-p1-gap-closure --strict
```
