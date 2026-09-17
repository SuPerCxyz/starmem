# StarMem

StarMem 是一个单用户、自托管、Raw-first 的个人 AI 记忆仓库：先保存原文和证据，再异步建立 Chunk、Embedding、Observation、Memory 和来源可追溯的 Ask 结果。AI 或外部服务故障不会阻断记录、Timeline、版本和 PostgreSQL 全文检索。

## 快速启动

```bash
cp .env.example .env
# 仅在未跟踪的 .env 或运行时环境中填写 STARMEM_CHAT_API_KEY（可选）
docker compose up -d --build
curl http://localhost:18000/health
```

Web 默认地址为 <http://localhost:18780>，API 为 <http://localhost:18000>。启动时 API 会执行 Alembic Migration 和幂等 seed，创建 `StarMem Native`、单用户管理员和内置 Prompt Registry。首次使用语义检索时，FastEmbed 会下载 `BAAI/bge-small-zh-v1.5` 的本地模型；模型不可用时自动保留 FTS 降级。

默认开发账号由 `.env` 的 `STARMEM_ADMIN_EMAIL` / `STARMEM_ADMIN_PASSWORD` 决定。生产部署必须替换密码和 Session Secret、启用 Secure Cookie，并限制 CORS 来源。

## 主要能力

- Capture：Markdown、代码、JSON/YAML、日志和 20,000+ 字符原文保存；支持 Ctrl/Cmd+Enter 快捷保存。
- Timeline：时间分组、cursor 分页、自定义起止日期、编辑、版本 Diff/恢复、Pin/Favorite、软删除。
- Entry 卡片：直接展示标签、多分类与逐项 AI 状态（索引/Embedding/分类/摘要/标签/实体/时间/项目/主题/Memory/关系/图片描述），失败项可重试。
- Search：PostgreSQL `tsvector`/GIN、`pg_trgm`/ILIKE、Chunk 向量检索和可配置 Hybrid；支持全文/语义/混合模式与类型/标签/实体/项目/主题/时间过滤；IP、UUID、WWN、Hostname、路径、错误码等精确命中优先。
- Related Entry：基于共享实体/标签、同 Project/Topic/Error/Host 与语义相似度的确定性相关记录，并返回命中理由。
- Source：Native Source 与未来外部只读快照共用 Source/ExternalItem/ContentUnit/Provenance。
- P1 Import：URL 快照、TXT/Markdown/JSON/YAML/Log、PDF 页级提取、图片本地 OCR、原始附件和 Inbox 重试。
- Native Portability：从 More 页面导出 Markdown、JSON、JSONL、含附件 ZIP，并导入 StarMem 原生 JSON/JSONL 备份；重复记录安全跳过。
- AI：独立 Job、规则提取、可替换 Chat/Embedding/Reranker Provider、Prompt Registry、Draft/Testing/Production、严格 Schema 校验。
- Memory：Evidence、Observation、Memory Candidate、Canonical Memory 分层，支持 ADD/SUPPORT/SUPERSEDE/CONFLICT/MERGE/IGNORE、Salience、来源和并发 scope lock；支持确认、标记过期、删除与状态筛选。
- Prompt Studio：Draft 编辑（含 Layer 2 Task Prompt 与模型参数）、内置 Prompt 克隆、Preview、Draft 测试与用户自定义 Test Case。
- Ask：查询理解、时间提示、Hybrid Retrieval、来源/跳转和无来源拒答。
- Knowledge Workbench：Project/Topic/Entity 聚合与管理（重命名/合并/排除/恢复）、Saved Search、Smart View（含「最近常问」）、时间回顾、Derived Knowledge Summary、本地安全扫描和相似 Entry 建议。
- Curation：Entry 相关记录跳转、AI Metadata 人工编辑与用户锁定、Inbox 标题/类型修正、批量重处理与全库 Embedding 重建。
- Optional AI：可配置 Reranker（默认关闭、失败回退）与图片描述 Provider（默认关闭、无模型时降级为 OCR）。
- PWA：standalone manifest、Safe Area、移动五项底部导航、草稿自动保存、同源 Share Target 和 Service Worker。

## 开发与验证

```bash
docker compose exec api pytest -q
docker compose exec api ruff check app tests alembic
docker compose build web
```

Web/API 端口在 `docker-compose.yml` 中显式绑定 `0.0.0.0`，默认对局域网开放：Web `http://<host-ip>:18780/`、API `http://<host-ip>:18000/`；PostgreSQL 与 Redis 只在 Compose 内部网络可达。API 文档位于 <http://localhost:18000/docs>。常用接口包括 `/api/v1/entries`、`/api/v1/search`、`/api/v1/ask`、`/api/v1/ai-jobs`、`/api/v1/prompts`、`/api/v1/memories`、`/api/v1/projects`、`/api/v1/smart-views`、`/api/v1/saved-searches` 和 `/api/v1/knowledge`。API Token 可在 `/api/v1/auth/tokens` 创建，明文只返回一次。

Embedding 重建：

```bash
docker compose exec api python -m app.rebuild_embeddings
```

附件默认保存在 Compose 的 `starmem-storage` volume，大小、URL 抓取和 OCR 语言可通过 `.env` 配置。P1 导入接口为 `/api/v1/ingest/url`、`/api/v1/ingest/file` 和 `/api/v1/inbox`。

安全扫描默认在本地执行；Entry 展开时可查看类型/位置摘要，旧记录可调用 `/api/v1/entries/{id}/safety/rescan` 补扫。任务模型路由通过 `/api/v1/settings` 的 `model_routing` 配置，只填写 provider/model，不填写凭据；优先级和重生成说明见 [`docs/implementation/phase-p1-workbench.md`](docs/implementation/phase-p1-workbench.md)。

备份和恢复说明见 [`docs/BACKUP_AND_OPERATIONS.md`](docs/BACKUP_AND_OPERATIONS.md)，Chat 配置和安全注意事项见 [`docs/LOCAL_LLM.md`](docs/LOCAL_LLM.md)。
P1 输入与导入实施记录见 [`docs/implementation/phase-p1-ingestion.md`](docs/implementation/phase-p1-ingestion.md)。
P1 Knowledge Workbench 记录见 [`docs/implementation/phase-p1-workbench.md`](docs/implementation/phase-p1-workbench.md)；移动端 Share Target 记录见 [`docs/implementation/phase-p1-mobile-share.md`](docs/implementation/phase-p1-mobile-share.md)。
P1 Native Portability 记录见 [`docs/implementation/phase-p1-portability.md`](docs/implementation/phase-p1-portability.md)。
P1 Gap Closure 记录见 [`docs/implementation/phase-p1-gap-closure.md`](docs/implementation/phase-p1-gap-closure.md)。
P1 设计对齐闭环记录见 [`docs/implementation/phase-parity-closure.md`](docs/implementation/phase-parity-closure.md)。
后续大模型接续开发请先阅读 [`docs/DEVELOPMENT_STATUS.md`](docs/DEVELOPMENT_STATUS.md)。
Agent 开发规则见 [`AGENTS.md`](AGENTS.md)；README 与 Agent 规则分别维护。

## 范围边界

当前已完成 P0 基础层和已确认范围内的 P1 输入/导入、Knowledge Workbench、移动端 Share Target、Native Portability。具体外部 Connector、CLI/MCP、浏览器插件、多人/RBAC、Graph UI、Kubernetes、微服务拆分、高级 Consolidation、主动提醒及多数据源同步仍按路线后置；相关 Adapter Contract、Source 边界和 Ingestion Job 仅作为后续扩展边界。
