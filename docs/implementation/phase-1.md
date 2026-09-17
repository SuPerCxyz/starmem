# Phase 1 实施记录

## 实际完成

- Compose 启动 `web`、`api`、`worker`、PostgreSQL/pgvector 和 Redis。
- Alembic `0001_initial_schema`、`0002_content_unit_fts`、`0003_vector_indexes`、`0004_memory_candidates` 可重复执行。
- Capture 事务写入 Entry、EntryVersion、`StarMem Native`、ContentUnit 和独立 AI Job；队列失败不回滚 Raw。
- Timeline 使用 cursor，Entry 编辑写不可变版本，支持 Diff、Restore、Pin、Favorite 和软删除。
- PostgreSQL FTS/GIN、pg_trgm/ILIKE 支持 WWN、UUID、Hostname、路径等技术内容。
- Web 已验证 Capture、Timeline、Markdown/代码展示、复制、编辑、软删除和 375px 移动底部导航；长代码块在自身容器滚动。

## 实际验证

```text
docker compose up -d --build
curl http://localhost:18000/health
docker compose exec api pytest -q
```

当前后端测试包含 Raw capture、20,000+ 字符保留、Markdown/代码块、WWN 精确搜索、三次编辑、版本 Diff/Restore、软删除、Native Source 和外部 Fixture。最终容器结果为 `20 passed`；Compose `/health` 返回 database/redis 均为 true。

浏览器验收使用本地 Chromium：375×812 视口无横向溢出，五项底部导航可见；实际 iPhone Safari/Home Screen 安装仍需真机验证。

## 已知限制

本阶段不实现具体外部 Connector、附件/OCR、多人权限和依赖 Chat 的派生任务；这些属于后续 P0 阶段或明确排除项。AI/Embedding 不可用时 Raw、Timeline、版本和 FTS 仍可用。
