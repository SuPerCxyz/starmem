## Why

StarMem 当前只有 v2 产品和工程规范，没有可运行实现。需要把“零整理记录、可追溯检索、长期 Memory 演化”落地为单用户自托管 P0，且原始记录不能依赖 AI 或外部模型才能保存。

## What Changes

- 从零建立 Docker Compose 项目骨架：React/Vite Web、FastAPI API、PostgreSQL/pgvector/pg_trgm、Redis Worker、Alembic、认证、日志、备份和测试入口。
- 实现 Capture、Timeline、Markdown/代码块、Entry CRUD、软删除、版本历史和 PostgreSQL 全文搜索。
- 实现结构化 Chunk、可替换 Embedding Provider、Semantic Search、可配置 Hybrid Search、精确标识符优先和统一 Source/ContentUnit/Provenance。
- 实现异步 AI Enrichment、Prompt Registry/Version/User Instructions/Schema Validation/Golden Dataset，以及可重试、幂等的 AI Jobs。
- 实现 Evidence/Observation/Memory/Knowledge 分层、Salience、Memory Reconcile 有限操作集、来源证据、生命周期、冲突和并发保护。
- 实现 Ask/RAG、Query Understanding、时间检索、事实/推断区分和原始来源引用。
- 实现桌面与移动 Web：PWA manifest、standalone、Safe Area、移动底部导航、触摸可用控件和草稿保护。
- 将用户提供的 OpenAI-compatible Chat Provider 作为默认 Chat 配置记录；真实 API Key 仅通过运行时环境变量读取，不进入仓库。

## Capabilities

### New Capabilities

- `capture-and-search`: 原始记录、时间线、版本、全文/语义/混合搜索和结果高亮。
- `ai-enrichment-memory`: AI 任务、结构化观测、Memory 生命周期、Salience、Reconcile、证据和 Ask/RAG。
- `prompt-studio`: Prompt Registry、版本、用户指令、Schema Contract、测试集、回滚和派生结果追踪。
- `source-provenance`: Native/External Source、External Item、ContentUnit、Search Scope、Provenance 和 Ingestion Job 基础模型。
- `mobile-pwa`: 响应式移动布局、PWA standalone、Safe Area、底部导航和草稿保护。
- `platform-operations`: Docker Compose、认证、配置、Provider 抽象、任务重试、可观测性、备份恢复和测试基础设施。

### Modified Capabilities

- None.

## Impact

- 新建整个应用目录、数据库迁移、API、Web、Worker、Prompt 资源、测试、脚本和文档。
- 新增运行时依赖：React/TypeScript/Vite、FastAPI/SQLAlchemy/Alembic/Pydantic、PostgreSQL 扩展、Redis/Dramatiq，以及一个小型本地多语言 Embedding 运行时/模型。
- 新增 `/api/v1/entries`、`/api/v1/search`、`/api/v1/ask`、`/api/v1/memories`、`/api/v1/ai/jobs` 等公共接口。
- P1/P2 能力仅保留可替换接口，不实现具体外部 Connector、附件/OCR、CLI/MCP、多人协作或知识图谱 UI。
