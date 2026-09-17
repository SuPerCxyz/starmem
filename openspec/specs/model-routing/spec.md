# model-routing Specification

## Purpose
让不同 AI 任务可以独立选择可替换的 Provider/model，同时保持 Prompt、Job Provenance、运行时凭据和无模型降级边界清晰可审计。
## Requirements
### Requirement: Task model routing is configurable without secrets

系统 MUST 支持按 classification、summary、memory、chat、embedding、reranker 等任务配置 Provider/model 路由；设置和 API 响应 MUST 不包含 API Key、Authorization Header 或完整连接凭据。

#### Scenario: Route summary to a configured model

- **WHEN** 用户为 summary 设置 Provider/model 并重新处理 Entry
- **THEN** 新 AI Job 使用该路由（若 Provider 可用），并在 Job/Derivation Provenance 中记录最终 Provider/model

#### Scenario: Route is unavailable

- **WHEN** 配置的路由没有凭据或 Provider 不可用
- **THEN** 该任务失败且原因可见，Raw、FTS 和其他可用任务不受阻断

