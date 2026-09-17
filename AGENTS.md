# StarMem 项目 Agent 规则

本文件是 StarMem 仓库级的项目补充规则。平台、会话和用户最新明确要求优先于本文件；本文件不替代全局 Agent 规则，也不重复复制全局规则全文。

## 必读资料与事实源

开始接续开发前按顺序阅读：

1. 本文件。
2. [`README.md`](README.md)：项目用途、启动和使用入口。
3. [`docs/DEVELOPMENT_STATUS.md`](docs/DEVELOPMENT_STATUS.md)：当前进度、验证结果、已知限制和交接状态。
4. 与任务相关的 `openspec/changes/`、`openspec/specs/` 和阶段实施文档。

涉及 `starmem_v2_complete_docs` 的新需求时，必须全量阅读目录内 5 个文档，不得做最小扫描或截断阅读：

- `STARMEM_V2_CHANGES.md`
- `STARMEM_V2_README.md`
- `starmem_v2_feature_list.md`
- `starmem_v2_prd_architecture.md`
- `starmem_v2_codex_implementation_prompt.md`

需求以用户最新明确要求为准；代码、实际运行结果和有效 OpenSpec 用于核对事实，不得用旧阶段文档覆盖当前实现事实。

## 当前项目边界

- 产品是单用户、自托管、Raw-first 的个人 AI Memory Repository。
- P0 和已确认范围内的 P1 输入/导入、Knowledge Workbench、Mobile Share Target、Native Portability 已完成；不要重复实现或回退这些能力。
- P1 的具体 External Connector、CLI/MCP、浏览器插件、多人/RBAC，以及 P2 的 Graph、Evolution、高级 Memory Consolidation、多源同步、主动能力和第三方 ingestion 均后置。没有新的 Requirement Review 和用户确认，不得开始这些跨层能力。
- P1 输入阶段已经包含 URL、文件、PDF、OCR、Attachment 和 Inbox；后续只修复明确问题，不因历史报告中的旧状态重复建设。

## 实施约束

- 新增用户可见功能、公共 API、schema、迁移、依赖或跨层能力前，先输出 Requirement Review；中型及以上变更使用 OpenSpec。
- 保持 Raw-first、Source/ContentUnit/Provenance、异步派生和“AI 故障不阻断原文保存”的边界。
- 修改前检查工作区现状，保留用户或其他协作者已有改动；不得使用 `git reset --hard`、`git clean` 或覆盖式恢复。
- 未经明确授权不得 commit、amend、push、merge、rebase 或改变远程 Git 状态。当前工作区可能没有 Git 元数据。
- API Key、Session Secret、密码、Cookie、Authorization Header 和完整敏感日志只允许存在于运行时环境；不得写入代码、文档、镜像、前端 bundle、测试输出或备份。
- 用户提供的 Chat 配置只记录 Base URL/model 等非敏感信息；具体 Key 永远不落盘、不回显。

## 本地运行与验证

```bash
docker compose up -d --build
curl http://localhost:18000/health
docker compose exec -T api pytest -q
docker compose exec -T api ruff check app tests alembic
docker compose exec -T api ruff format --check app tests alembic
docker compose build web
scripts/smoke.sh
```

涉及 Web、PWA、移动端或用户可见交互时，追加：

```bash
STARMEM_TEST_EMAIL=admin@starmem.local \
STARMEM_TEST_PASSWORD=change-this-password \
python3 tests/playwright_smoke.py
```

完成前必须检查真实用户链路、边界/异常路径、OpenSpec 状态、敏感信息、临时文件和测试数据；测试结果必须记录实际命令和实际输出，不能把静态阅读或预期结果写成通过。

## 文档分工

- `README.md`：面向人类开发者和使用者，记录项目介绍、快速启动、主要能力、常用入口和范围概要。
- `AGENTS.md`：面向 Coding Agent，记录稳定的仓库规则、必读资料、开发边界、安全门禁和验证入口。
- `docs/DEVELOPMENT_STATUS.md`：面向后续 Agent 的动态进度交接，记录已完成任务、验证数字、运行状态、限制和下一步候选。
- `docs/implementation/phase-*.md`：记录各阶段实际实现与验证结果。
- `openspec/changes/`：中大型变更的 proposal/design/spec/tasks；任务勾选不能替代代码和测试事实。

阶段完成或验证数字变化后，应同步更新 `docs/DEVELOPMENT_STATUS.md` 和对应阶段文档；README 只维护稳定的使用说明和能力概览，不把临时调试过程写入其中。
