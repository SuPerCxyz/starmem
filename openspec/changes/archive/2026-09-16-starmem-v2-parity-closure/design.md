## Context

设计文档审计确认的剩余缺口集中在交互闭环与派生数据可用性，不涉及架构方向变化。既有边界必须保持：Raw-first、Source/ContentUnit/Provenance、异步派生、AI 故障不阻断原文保存。

## Goals / Non-Goals

**Goals:**

- 补齐设计文档 P0 与已确认 P1 中缺失的用户可见行为。
- 让派生数据（标签、多分类、Related 信号、Memory 状态、Prompt 测试）可读、可改、可解释。
- 用遍历式端到端测试证明按钮点击后的逻辑闭环。

**Non-Goals:**

- 不实现 CLI、MCP、浏览器插件、External Connector、第三方导入。
- 不实现离线查看/离线写入、Web Push、App Badge、相机、语音、Passkey。
- 不实现 P2（Graph UI、Evolution、Consolidation、多源同步、主动能力）。

## Decisions

### 1. 多分类以 JSON 列保存，主分类保留

新增 `entries.content_types`（JSONB，默认空数组）。读取时若为空则回退为 `[content_type]`，避免回填迁移。AI 判定多分类写入 `content_types`，`content_type` 仍写主分类；用户编辑后记录 `content_types_locked` 语义（以 Observation 或列内标记实现），AI 重跑不覆盖。

### 2. Related 信号在服务层确定性计算

在既有 `relations` 读取之外新增信号计算：共享实体（EntryEntity）、共享标签（EntryTag）、同 Project/Topic（Observation）、同 Error/Host（Entity 类型）。每个候选返回 `reasons` 与 `score`，多信号加权；无语义可用时仍能给出确定性结果。

### 3. 逐项 AI 状态由现有 AIJob 聚合

复用 `ai_jobs`，按固定顺序（chunk/embedding/classify/tag/entity_extract/memory_extract）映射为可读状态，返回每项 status 与 error，失败项复用既有单 Job 重试接口。

### 4. Memory 生命周期复用状态机

`expired` 已存在于状态枚举但无人写入。新增标记过期操作写入 `valid_to`/状态，保留证据与 supersede 关系；删除继续复用软删除语义。

### 5. Prompt Studio 扩展复用现有版本机制

克隆内置 Prompt 通过 `create_draft` 生成含 Task Prompt 的 Draft；模型参数作为版本字段保存；Test Case 使用既有 `prompt_test_cases` 表，用户用例 `is_builtin=false`。

### 6. 时间线日期范围使用既有查询参数

后端 `entries` 已支持 `start`/`end`，前端增加日期输入并复用同一 query key，不新增接口。

## Risks / Trade-offs

- 多分类增加 JSON 列，检索需同时匹配主分类与集合，注意索引与查询成本。
- Related 信号为多次查询，需限制候选数量避免放大延迟。
- Prompt Studio 允许编辑 Task Prompt 时需保持安全契约只读，避免用户绕过系统约束。

## Migration Plan

1. Alembic 迁移新增 `entries.content_types`，默认空数组，不强制回填。
2. 后端服务、Schema、API 增量扩展，保持既有契约兼容。
3. Web 交互补齐。
4. 后端测试 + Playwright 遍历测试 + 文档更新，验证通过后再归档。

## Open Questions

无。
