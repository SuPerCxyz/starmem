# StarMem v2 P0 完成报告

## 范围

本次按 `starmem_v2_complete_docs` 的 P0 要求，从空仓库实现了单用户、自托管、Raw-first 的 StarMem 基础系统。P1/P2 的具体外部 Connector、附件/OCR、CLI/MCP、多人/RBAC、Graph UI、Kubernetes 和微服务拆分明确排除。

## 已交付

- Compose 运行底座：FastAPI、Dramatiq Worker、PostgreSQL/pgvector/pg_trgm、Redis 和 Nginx Web。
- Raw Capture/Timeline：事务性 Entry、不可变版本、Diff/Restore、cursor 分页、日期/Pin/Favorite、软删除恢复。
- Search：PostgreSQL FTS、trigram/ILIKE、FastEmbed `BAAI/bge-small-zh-v1.5` 512 维语义检索和 Hybrid；技术标识符精确命中优先。
- Source/Provenance：Native Source、ExternalItem/ContentUnit 外部只读快照边界、Chunk/Memory 来源追溯。
- AI：独立 AI Job、规则提取、可替换 Chat/Embedding/Reranker Provider、严格 Prompt Schema、Draft/Testing/Production、Golden Dataset 和失败隔离。
- Memory：Observation、Memory Candidate、Canonical Memory、Salience、Retrieve-Before-Write、有限 Reconcile 操作、scope advisory lock、支持/冲突/替代来源。
- Ask：Query Understanding、时间提示、来源限定、Active Memory/Hybrid 上下文、无来源拒答、事实/推断标识和原文跳转。
- Web/PWA：桌面侧栏、移动五项导航、375/768/1024/1440 响应式布局、Safe Area、草稿恢复、manifest、Service Worker 预留和设置/Prompt Studio/Job/Memory 页面。
- 运维：结构化 secret-safe 日志与指标、备份/显式确认恢复、Embedding 重建和集成 smoke 脚本。

## 最终验证记录

以下命令均在最终代码状态执行：

```text
docker compose exec -T api ruff format --check app tests alembic
docker compose exec -T api ruff check app tests alembic
docker compose up -d --build api worker
docker compose exec -T api pytest -q                 # 20 passed, 2 warnings
docker compose build web
docker compose up -d web
scripts/smoke.sh                                    # integration-smoke: passed
curl http://localhost:18000/health                   # database/redis true
docker compose exec -T api alembic current           # 0006_user_metadata_overrides (head)
python3 tests/playwright_smoke.py                    # playwright-smoke: passed
```

Playwright 验收覆盖登录后 Capture→Search→原文跳转、Ask 来源、Prompt Studio、PWA manifest、375/768/1024/1440 视口无横向溢出和登录后的浏览器错误检查。备份脚本此前已生成 PostgreSQL dump，并用 pgvector 镜像检查了 `entries`、`content_units`、`memory_candidates`、`prompt_versions` 条目。

## 凭据与限制

用户提供的 Chat Key 未写入仓库、镜像、前端、日志或备份；工作区没有 `.env`，运行时状态接口因此显示 `chat_configured=false`。已验证 Chat endpoint/model 的配置路径和关闭 thinking 参数，但未在本次验收中使用真实 Key 生成远程答案。FastEmbed 本地模型已实际加载并用于 512 维语义检索。

真实 iPhone Safari 的键盘、网络切换和 Home Screen 安装仍需实体设备补验；本地 Chromium 响应式验收不能替代真机结论。恢复脚本是显式确认后的覆盖操作，本次未执行恢复。

## Performance

2026-09-15 在本地 Compose 环境使用 `scripts/benchmark.py` 实测（PostgreSQL + pgvector，FastEmbed `BAAI/bge-small-zh-v1.5`），规模为 2,000 Entry / 200 个已嵌入 Chunk、每项 20 次采样：

```text
python scripts/benchmark.py --entries 2000 --chunks-per-entry 4 --embedding-entries 200 --samples 20 --json /tmp/starmem-benchmark-2000.json

raw_save  p50 4.64ms   p95 12.62ms
fts       p50 82.10ms  p95 118.88ms
hybrid    p50 107.09ms p95 126.61ms
ask_local p50 26.97ms  p95 31.39ms
```

说明与降级：

- 目标是 100k Entry / 500k Chunk；本机 Compose 单实例在当前资源下未运行该规模，故按 2,000 Entry 如实记录，未宣称达标。
- `ask_local` 关闭远程 Chat Key，仅测量本地检索与来源拼装；远程生成延迟不在此基线内。
- 基准 fixture 带独立 run marker，运行结束后自动清理，不残留用户数据。
