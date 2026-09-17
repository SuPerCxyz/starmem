## Context

P0/P1 已具备 Entry/版本/ContentUnit/AIJob/Memory/Prompt/Search/Ask/Workbench/Ingestion/Portability 等能力。本 change 只补齐「已完成范围内的真实缺口」，不改动 Raw-first、Source/ContentUnit/Provenance、异步派生和 AI 故障不阻断原文保存这些边界。

## Goals / Non-Goals

**Goals:**

- 让已产生的派生数据（Relation、Observation、Project/Topic）可被用户读取和修正。
- 让人工修改具备持久优先级，AI 重跑不覆盖用户决定。
- 让批量与全库维护操作可用且有界、可回退、可观察。
- 把可选增强（Reranker、图片描述、查询日志）做成默认关闭、失败可降级的扩展点。
- 用真实可复现证据回填性能与完成标准，完成 OpenSpec 生命周期收尾。

**Non-Goals:**

- 不实现多人/RBAC、外部 Connector、CLI/MCP、浏览器插件。
- 不实现 P2 高级能力（Graph UI、Evolution、Consolidation、多源同步、主动能力）。
- 不让 AI 自动修改或删除 Raw Entry，不以派生数据替代原始证据。

## Decisions

### 1. 人工编辑以 user-locked 语义实现

`Observation.is_user_locked`、`EntryTag.user_confirmed/user_removed`、`EntryEntity.source="user"` 已存在，新增内容类型字段编辑统一写为用户来源标记；AI 重跑时跳过 user-locked 观测、user_confirmed 标签和 user 来源实体，不物理删除 AI 记录。Summary/类型/Project/Topic 通过新增/更新用户观测实现，保留 AI 观测用于对比。

备选方案是覆盖 AI 观测；会丢失「AI 曾如何判断」的可追溯性，因此不采用。

### 2. Relation 读取复用既有表

`Relation` 已由 `relation_build` 写入，只缺读取出口。新增 `GET /api/v1/entries/{id}/relations` 返回出边与入边、关联 Entry 摘要、类型与置信度；不新增表结构。

### 3. Project/Topic/Entity 管理采用显式操作

重命名更新名称与关联观测；合并把源对象的观测重指向目标对象并软标记源对象 `status="merged"`；排除把对象标记为 `status="excluded"` 并从默认列表隐藏，原始 Entry/观测保留。所有操作需要写入权限与 CSRF，且记录 `metadata_json` 审计字段。

### 4. Inbox 修正写到 Entry，不复制附件

修正标题与内容类型直接更新 Entry 并追加 EntryVersion；原始附件、ContentUnit 与 provenance 保持不变。这样避免出现两份原文。

### 5. 图片描述作为可选 Provider

新增 `ImageDescriptionProvider` Protocol 与 `STARMEM_IMAGE_DESCRIPTION_ENABLED`（默认 false）。启用且模型可用时生成 `image_description` 观测并写入派生；不可用时保持 OCR 文本与处理状态，明确在 Entry 上显示降级原因，不阻断原文保存。

### 6. 批量重处理有界且幂等

新增 `POST /api/v1/entries/reprocess-batch` 接受显式 ID 列表（上限 200）或过滤器（source_scope、日期、content_type），逐个复用 `reprocess_entry` 与既有 generation/唯一约束；返回 submitted/failed 计数。全库重建通过既有 `rebuild_embeddings` 命令与新增 `POST /api/v1/maintenance/rebuild-embeddings` 触发，均不复制数据。

### 7. Reranker 默认关闭并回退

新增 `STARMEM_RERANKER_PROVIDER`（默认 none）与可选 HTTP Reranker 实现；Hybrid 排序后如启用则重排前 N 条，异常或超时记录指标并保持原排序。Prompt 级 model_routing 中已有的 reranker 任务键继续生效。

### 8. Ask 查询日志脱敏有界

新增 `ask_queries` 表保存脱敏查询、source_scope、结果计数、耗时与创建时间，不保存答案正文与来源内容。新增「最近常问」Smart View 聚合最近 30 天高频查询（相同脱敏查询计数），空数据时返回空列表而非报错。

### 9. 性能基线与完成标准

新增 `scripts/benchmark.py`，支持 `--entries`/`--chunks` 参数，在可控数据量下测量 Raw 保存、FTS、Hybrid、Ask 本地检索延迟并输出 JSON；文档记录实际环境、数据规模与是否达到 100k/500k 目标或降级原因。回填 P0 完成标准清单并 archive 五个既有 change，同步主 spec。

## Risks / Trade-offs

- 批量重处理会新增大量 AI Job；限制单次上限并在文档中说明队列容量。
- 合并 Project/Topic 会改变后续聚类语义；操作需要显式确认并记录审计字段，不自动合并。
- 图片描述依赖外部模型质量；默认关闭，避免在无凭据环境引入失败面。
- Ask 日志属于新增数据；只保存脱敏查询与统计，遵循既有 secret-safe 约束。
- 性能基线与真机验收受本机资源限制；文档必须如实标注降级与未验证项。

## Migration Plan

1. 新增 Alembic migration（ask_queries 表与必要索引），保持向后兼容。
2. 新增/扩展服务、API、Worker 与前端入口。
3. 更新配置、README、DEVELOPMENT_STATUS、阶段文档与 OpenSpec 工件。
4. 运行后端测试、lint/format、Web 构建、Compose smoke、Playwright 与基准脚本并记录真实结果。
5. archive 已完成的五个 change 并同步主 spec；本 change 在验证通过后 archive。
