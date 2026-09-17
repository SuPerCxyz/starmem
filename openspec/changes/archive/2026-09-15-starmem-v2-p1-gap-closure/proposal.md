## Why

P0 与已确认 P1 范围虽然任务全部勾选，但按原始产品清单逐条核对后仍存在真实缺口：Relation 只写不读、AI Metadata 无法人工编辑、Project/Topic 缺少人工管理、Inbox 只能重试、图片只有 OCR 没有描述、批量重处理、Reranker、Smart View「最近常问」、性能基线以及 OpenSpec 生命周期收尾都未落地。这些缺口会让已完成能力在实际使用中不完整。

## What Changes

- 新增 Relation 读取 API 与 Entry 详情「相关记录」展示，让 relation_build 结果可用。
- 新增 AI Metadata 人工编辑：标签、类型、项目、Topic、Summary、Entity、Importance，并保证人工修改后 AI 重跑不覆盖。
- 新增 Project/Topic 管理：重命名、合并、排除错误归类，以及 Entity 合并。
- 新增 Inbox 手工修正：修正标题与分类並写回 Entry，保留原始附件。
- 新增可插拔图片描述 Provider 与 image_describe 派生，无模型时降级为 OCR 文本并明确提示。
- 新增批量重处理：按过滤器选择一个或多个 Entry 重新分析、重建 Embedding、Related，并支持全库重建。
- 启用可配置 Reranker（默认关闭），Hybrid 检索后可重排，失败自动回退。
- 新增 Ask 查询日志（脱敏、有界）与 Smart View「最近常问」。
- 新增性能基准脚本与 P0 Performance 记录，覆盖 100k Entry / 500k Chunk 目标或如实降级。
- 回填 P0 完成标准清单，archive 已完成 change 并同步主 spec。

## Capabilities

### New Capabilities

- `entry-relations`: Relation 读取、相关记录 API/UI 与置信度展示。
- `metadata-curation`: 人工可编辑 AI Metadata、user-locked 语义、Project/Topic/Entity 管理与 Inbox 修正。
- `batch-reprocessing`: 有界批量重处理与全库重建入口。
- `reranking`: 可配置 Reranker 与 Hybrid 重排回退。
- `image-description`: 可插拔图片描述 Provider 与降级路径。
- `ask-analytics`: 脱敏 Ask 查询日志与「最近常问」Smart View。
- `performance-baseline`: 可复现实基准脚本与性能记录。

### Modified Capabilities

- `knowledge-workbench`：新增「最近常问」Smart View，复用现有稳定性定义。
- `ai-enrichment-memory`：新增 image_describe 派生与 Reranker 路由；人工编辑优先级高于 AI 重跑。
- `platform-operations`：新增基准脚本、OpenSpec archive 与完成标准回填。

## Impact

- Backend：新增 Alembic migration（查询日志、Relation 查询索引沿用既有表）、关系/元数据/批量/重排/图片描述/查询日志服务与 API；不破坏既有 Entry、Search、Ask、Memory 契约。
- Web：Entry 详情新增相关记录与 Metadata 编辑面板；Inbox 新增修正；Workbench/More 新增批量重处理与项目/主题管理入口。
- AI/Privacy：图片描述默认关闭；Ask 查询日志只保存脱敏查询与结果计数；Reranker 默认关闭且失败回退既有排序。
- Tests/Docs：新增单元与集成测试、Playwright 路径、基准脚本、README/DEVELOPMENT_STATUS/阶段文档更新与 OpenSpec archive。
- 明确排除：多人/RBAC、External Connector、CLI/MCP、浏览器插件、P2 高级能力（由后续独立 change 承载）。
