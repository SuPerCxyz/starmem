## Purpose

提供可重复启动、可配置、可观测和可测试的单用户自托管运行基础，确保数据库、Worker、AI Provider 或外部服务异常时数据安全和故障可恢复。

## ADDED Requirements

### Requirement: The stack starts through Docker Compose
系统 MUST 提供 `web`、`api`、`worker`、`postgres` 和 `redis` 服务的 Docker Compose 启动方式，并通过 `.env.example`、Migration 和 README 说明初始化、认证、Provider、备份恢复和重处理。

#### Scenario: Start from a fresh checkout
- **WHEN** 用户复制 `.env.example` 为 `.env` 并执行 `docker compose up -d`
- **THEN** 所有必要服务启动，数据库 Migration 可执行，Web 可访问

### Requirement: Health and authentication are explicit
系统 MUST 提供 `/health` 检查 API、数据库和 Redis；P0 使用单用户认证、密码 Hash、HttpOnly/Secure/SameSite Session Cookie、CSRF 防护、Rate Limit、CORS 白名单和可撤销 API Token。

#### Scenario: Health reports a dependency failure
- **WHEN** Redis 或数据库不可用并请求 `/health`
- **THEN** 响应明确标记对应依赖失败，不伪装为健康

### Requirement: Chat and embedding providers are replaceable
系统 MUST 将 Chat、Embedding 和 Reranker 抽象为可替换 Provider，所有外部调用有 timeout、有限重试、backoff 和失败状态；默认 Chat 配置可使用已验证的 OpenAI-compatible endpoint，但 API Key 只能来自运行时环境变量。

#### Scenario: Use the supplied chat provider safely
- **WHEN** Worker 执行需要 Chat 的 AI Job
- **THEN** 使用配置的 qwen35-4b Chat Provider，并默认发送 `enable_thinking=false`；日志和仓库文件不包含 API Key

#### Scenario: Missing embedding provider
- **WHEN** 未配置可用 Embedding Provider
- **THEN** Raw 保存、全文搜索和其他非语义流程仍可用，Semantic Search 明确报告不可用而不是伪造向量

### Requirement: Operations are observable without leaking secrets
系统 MUST 使用结构化日志并关联 request_id、job_id、entry_id、Provider、模型、耗时、token usage、重试次数、搜索耗时、Embedding 耗时和错误类型；日志不得包含 Secret、完整原文凭据或 API Key。

#### Scenario: Trace a failed AI job
- **WHEN** AI Provider 超时
- **THEN** 可以按 request/job/entry 关联失败原因和耗时，且敏感内容被排除或脱敏

### Requirement: Backups preserve recoverable source data
系统 MUST 提供数据库、配置和附件（启用后）的备份/恢复脚本；Embedding 等可重建派生数据不应成为恢复原始数据的前置条件。

#### Scenario: Restore without embeddings
- **WHEN** 用户从不包含 Embedding 的备份恢复系统
- **THEN** Raw Entry、版本、Metadata、Memory 来源和配置可恢复，Embedding 可以通过重处理重建

### Requirement: Schema changes and core behavior are tested
系统 MUST 通过 Alembic Migration 管理 schema，提供 API、模型、搜索、Memory、AI、Worker 和集成测试；CI/测试不得依赖真实外部 AI API，并必须覆盖重试、超时、幂等、来源引用和并发 Reconcile。

#### Scenario: Run tests without network credentials
- **WHEN** 测试环境未提供真实 Provider Key
- **THEN** Mock Provider 完成测试，关键路径仍可验证，不因外部网络不可用而跳过测试
