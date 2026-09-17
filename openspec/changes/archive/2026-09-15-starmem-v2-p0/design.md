## Context

项目根目录目前只有需求文档，未有可复用代码或数据。实现必须从零建立单用户自托管应用，并同时满足“Raw Entry 先保存”和 P0 的移动端、外部来源、Prompt 与 Memory 约束。用户提供的 OpenAI-compatible 服务已验证支持 Chat Completions，但 `qwen35-4b` 的 `/embeddings` 返回 501；因此 Chat 与 Embedding 必须是独立 Provider。

## Goals / Non-Goals

**Goals:**

- 用一个可启动的 Compose 栈完成 API、Web、Worker、PostgreSQL 和 Redis 的闭环。
- 让没有 AI 时仍可 Capture、Timeline、版本管理和全文搜索。
- 用 ContentUnit 统一 Native/External 检索与 Provenance，使用 PostgreSQL 同时承载 FTS 和 pgvector。
- 让 AI 只产生经 Schema 验证的派生数据建议；Memory Apply 由确定性事务逻辑完成。
- 为用户提供可编辑、可测试、可回滚的 Prompt 版本和可追踪的 AI 派生结果。
- 使用 `fastembed` 懒加载小型本地多语言/中文 Embedding 模型 `BAAI/bge-small-zh-v1.5`，并允许配置其他 Provider。

**Non-Goals:**

- P0 不实现具体 External Connector、附件/URL/OCR、CLI、MCP、浏览器插件、离线同步或 Graph UI。
- 不引入 Elasticsearch、OpenSearch、MongoDB、Neo4j、Kubernetes、微服务拆分或团队权限。
- 不把用户提供的 API Key 写进仓库、文档、日志或生成的示例配置。

## Decisions

### 1. 单仓库、三应用进程

使用 `backend/`、`web/`、`worker/` 三个源码入口；Compose 只负责进程边界，不拆成多个独立领域服务。API 和 Worker 共享 backend 包，减少跨服务契约和部署复杂度。

备选方案是前后端分离的多个 Python package 或微服务；当前单用户规模不需要它们，且会增加 Migration、认证和本地调试成本。

### 2. PostgreSQL 是唯一核心数据源

使用 PostgreSQL 16 + `vector` + `pg_trgm`，通过 Alembic 管理 schema。Raw Entry、版本、ContentUnit、Observation、Memory、Prompt 和 Job 均落库；Redis 只作为异步消息传输，不保存事实数据。

FTS 使用 `tsvector`/GIN，并用 `pg_trgm` 和 ILIKE 作为技术标识符与中文片段的补充。Hybrid Search 在候选合并后做可配置加权和 exact identifier boost；没有 Embedding 时保留 FTS 路径并返回能力状态。

### 3. ContentUnit 作为检索边界

Native Entry 保存时立即生成一个原始 ContentUnit；后台 Chunk 后再生成结构化 ContentUnit/EntryChunk。External Item 使用相同的 ContentUnit 结构。每个检索结果通过 `source_id`、owner 信息和 snippet 生成统一 Provenance，Ask 不直接拼接 Entry 表字段。

### 4. Raw-first 的事务边界

创建 Entry 的 API 事务只写原文、EntryVersion、Native Source、原始 ContentUnit 和初始 Job 记录，然后立即返回。发送 Redis 失败只会把 Job 标记为 retryable/failed，不回滚 Raw Entry。所有重处理通过确定性的 `job_type + entry_id + generation` 约束和 upsert 保证幂等。

### 5. Provider 分离和本地 Embedding

定义同步 Python Protocol：`ChatProvider.complete_json`、`EmbeddingProvider.embed`、`RerankerProvider.rerank`。Chat Provider 采用 OpenAI-compatible HTTP，读取 `STARMEM_CHAT_BASE_URL`、`STARMEM_CHAT_MODEL` 和运行时 Key，默认发送 `chat_template_kwargs: {enable_thinking: false}`，timeout/重试由客户端统一处理。

Embedding 默认使用懒加载 FastEmbed，模型名和维度通过环境变量配置；模型下载失败不会阻塞 Raw/FTS。模型维度写入配置并在 Migration 中固定默认值，换模型时要求重建 Embedding。测试使用 Mock Provider，不访问真实 API。

### 6. 结构化 AI 与确定性 Memory Apply

Prompt 文本存放在 `prompts/` 资源并同步到 Prompt Registry，不在业务函数中散落。模型输出先用 Pydantic Schema 校验，再转成 Observation/Memory Candidate。Reconcile 只接受六种 Operation；程序按 `subject_key` 取得 PostgreSQL advisory transaction lock，在同一事务中执行 SUPPORT/SUPERSEDE/CONFLICT 等状态变化和 Memory Source 写入。Active Scope/Value 使用唯一索引辅助去重。

为降低小模型不稳定性，实体标识符和时间的明显模式先由确定性解析器提取，作为 Observation 输入；AI 失败仍显示 Failed，不伪称成功。对于可安全重建的派生表采用 generation/version 标记，人工覆盖字段保留锁定来源。

### 7. Prompt Studio 的安全边界

普通用户编辑 User Instructions 时创建 Draft Version；System Safety Contract 和 Output Schema 由服务端控制。测试只读取固定 Golden Dataset/用户 Test Case，不触发 Production 变更。Promote/Rollback 都是新版本或状态变更，旧版本永不删除。

### 8. 认证、会话和移动草稿

使用单用户初始化账号和数据库 Session；浏览器只拿 HttpOnly、SameSite、可配置 Secure 的 session cookie，CSRF 使用同源 token/header。API Token 只用于显式 API 客户端。Capture 草稿放在浏览器 IndexedDB/localStorage（仅草稿，不是认证凭据），提交成功后清除；服务端登录状态不依赖 localStorage Token。

### 9. Web UI 方向

采用 React/TypeScript/Vite，内容优先的 Swiss/Minimalism 视觉：高对比蓝色文本、橙色主操作、Atkinson Hyperlegible、桌面侧栏和移动五项以内底部导航。使用语义 CSS 变量和 SVG 图标；移动辅助 Metadata 用抽屉/折叠，代码块只在自身容器横向滚动，不撑破页面，并遵守 44px 触摸目标、focus 状态和 reduced-motion。

### 10. 验证策略

后端用 pytest 覆盖 API、模型、搜索、Memory、Provider、Worker 和集成路径；Mock Provider 覆盖 Schema 失败、超时、重试和幂等。前端用 TypeScript build/lint 和 Playwright 关键路径验证，检查 375px/768px/1440px 布局、Capture→保存→Timeline、搜索和来源跳转。真实 iPhone Safari 仍需在设备上补验。

## Risks / Trade-offs

- [小模型 JSON 输出不稳定] → 限制上下文和 token，关闭 thinking，使用严格 Schema/重试；失败时保留 Raw 并显示 Job 失败。
- [本地 Embedding 模型首次下载慢或不可用] → 懒加载、配置化、Mock 测试和 FTS 降级；文档明确首次下载与重建命令。
- [PostgreSQL 中文 FTS 分词有限] → 保留 ILIKE/trigram，技术标识符使用 exact boost；后续可替换 tokenizer 而不改 API。
- [单用户 Session Cookie 的部署安全依赖反向代理] → 默认开发环境可关闭 Secure，生产配置强制 HTTPS、Secure Cookie、CORS 白名单和限流。
- [大 P0 范围带来集成风险] → 严格按 Phase 验收，先 Raw/FTS，再 AI/Memory/Ask；每阶段保存实现记录和定向测试结果。

## Migration Plan

1. 使用 Compose 启动 PostgreSQL/Redis，执行 Alembic 初始 Migration 和内置 Source/Prompt seed。
2. 创建单用户管理员并通过 Web 登录；检查 `/health`、Capture、FTS 和 Job 状态。
3. 配置 Chat Provider Key（仅通过未跟踪运行时环境），按需下载本地 Embedding 模型。
4. 逐阶段启用 Chunk、Embedding、AI Enrichment、Memory 和 Ask；任何阶段失败都可以继续使用 Raw/FTS。
5. 回滚时停止 Worker、恢复 PostgreSQL 备份并运行对应 Alembic downgrade；派生 Embedding/Observation 可删除后重建，Raw/EntryVersion 不可删除。

## Open Questions

- 真实 iPhone Safari 和主屏幕安装必须在具备设备的环境中完成最终验收；本地浏览器只能验证响应式和 manifest 行为。
