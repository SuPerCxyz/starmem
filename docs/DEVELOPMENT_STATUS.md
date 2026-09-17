# StarMem v2 开发进度与接续说明

> 本文件是后续 Coding Agent 的交接入口。内容以当前工作区、实际运行结果和已确认的用户范围为准；如果它与旧的阶段记录冲突，应优先核对当前代码、OpenSpec 和最近验证结果。

更新时间：2026-09-16  
项目根目录：`/home/superc/code/starmem`  
产品形态：单用户、自托管、Raw-first 的个人 AI Memory Repository

## 1. 用户要求与硬边界

- 用户要求完整扫描并全量阅读 `starmem_v2_complete_docs`，不是最小扫描。
- 已全量读取以下 5 个事实源，共 9,701 行：
  - `STARMEM_V2_CHANGES.md`（43 行）
  - `STARMEM_V2_README.md`（37 行）
  - `starmem_v2_feature_list.md`（2,792 行）
  - `starmem_v2_prd_architecture.md`（3,824 行）
  - `starmem_v2_codex_implementation_prompt.md`（3,005 行）
- 核心原则：可靠保存优先于 AI；原始记录优先于派生信息；搜索质量优先于花哨 UI；答案必须能回到来源。
- 用户已确认继续实施已确认范围内的 P1/P2 路线。
- 用户明确认为外部 Connector、附件/OCR、多人权限、CLI/MCP、Graph 等跨层能力应后置。实际工作中，P1 输入阶段已先完成 URL/文件/PDF/OCR/附件闭环；后续不得再无确认扩大到跨层能力。
- 当前确认范围内已完成 P0 和主要 P1 能力；P2 路线以及明确后置的跨层能力不要自行开始。若要开始其中任何一项，先重新做 Requirement Review 并建立/更新 OpenSpec。
- 不得写入、输出或提交任何 API Key、Session Secret、密码、Cookie、Authorization Header 或完整敏感日志。
- 未执行 Git commit/push。当前工作区未发现可用 Git 仓库元数据，不要假设存在可提交的 Git 历史。

## 2. 总体进度

| 阶段/变更 | OpenSpec 任务 | 当前状态 | 主要记录 |
| --- | ---: | --- | --- |
| P0 基础实现 | 68/68 | 已完成 | `openspec/changes/starmem-v2-p0`、`docs/P0_COMPLETION_REPORT.md` |
| P1 输入与导入 | 21/21 | 已完成 | `openspec/changes/starmem-v2-p1-ingestion`、`docs/implementation/phase-p1-ingestion.md` |
| P1 Knowledge Workbench | 21/21 | 已完成 | `openspec/changes/starmem-v2-p1-knowledge-workbench`、`docs/implementation/phase-p1-workbench.md` |
| P1 Mobile Share Target | 9/9 | 已完成 | `openspec/changes/starmem-v2-p1-mobile-share`、`docs/implementation/phase-p1-mobile-share.md` |
| P1 Native Portability | 8/8 | 已完成并归档 | `openspec/changes/archive/2026-09-15-starmem-v2-p1-portability`、`docs/implementation/phase-p1-portability.md` |
| P1 Gap Closure | 24/24 | 已完成并归档 | `openspec/changes/archive/2026-09-15-starmem-v2-p1-gap-closure`、`docs/implementation/phase-p1-gap-closure.md` |
| P1 设计对齐闭环 | 25/25 | 已完成并归档 | `openspec/changes/archive/2026-09-16-starmem-v2-parity-closure`、`docs/implementation/phase-parity-closure.md` |
| UI Preline 视觉迁移 | 35/36 | 已完成并归档 | `openspec/changes/archive/2026-09-16-starmem-v2-ui-preline-refactor`（spec: `ui-design-system`） |
| UI V2 页面架构重构 | 33/36 | 已完成并归档 | `openspec/changes/archive/2026-09-16-starmem-ui-v2-page-architecture`、`docs/ui/STARMEM_UI_V2_COMPLETION.md` |
| 全站 UI Composition 重构 | 8/8 | 已完成 | `openspec/changes/starmem-full-site-composition`、`docs/ui/STARMEM_FULL_SITE_COMPOSITION_REPORT.md` |
| UI Tabler 严格模板迁移 | 30/30 | 已完成 | `openspec/changes/starmem-tabler-migration`、`docs/ui/STARMEM_TABLER_MIGRATION_REPORT.md` |
| UI Tabler Typography 一致性与自动校验 | 14/14 | 已完成 | `openspec/changes/starmem-tabler-typography`、`docs/ui/STARMEM_TABLER_TYPOGRAPHY_REPORT.md` |
| UI Tabler 字体真实生效验证 | 15/15 | 已完成 | `openspec/changes/starmem-tabler-font-verification`、`docs/ui/STARMEM_TABLER_FONT_VERIFICATION_REPORT.md` |
| P2 高级路线 | 未开始 | 按用户确认后置 | Graph、Evolution、Consolidation、多源同步、主动能力等 |

P0 与 4 个 P1 change 已归档到 `openspec/changes/archive/2026-09-15-*`，delta 已同步为 `openspec/specs/` 主 spec；P1 Gap Closure 亦在验证通过后归档；P1 设计对齐闭环归档在 `openspec/changes/archive/2026-09-16-starmem-v2-parity-closure`。`openspec validate --all --strict` 当前为 33 passed / 0 failed。完成事实以代码、运行行为和验证结果为准，任务勾选不能替代验证。

归档目录中的 `tasks.md` 是归档当时的事实快照；最终验证记录见 `docs/implementation/phase-p1-gap-closure.md`。

### 2.0 UI V2 页面架构重构（2026-09-16，历史记录）

以下记录对应 Tabler 迁移前的 Preline 阶段；当前视觉 Source of Truth、实现和验证以 2.4 及 `docs/ui/STARMEM_TABLER_MIGRATION_REPORT.md` 为准。

用户确认执行「统一 StarMem 页面母版与信息架构」。change：`starmem-ui-v2-page-architecture`（`openspec validate --strict` 通过）。视觉继续严格来自 Preline，未新增任何自定义 CSS（`styles.css` 保持 48 行）。

关键改动：

- 新增 `web/src/components/ui.tsx`：`PageHeader` / `FilterBar` / `EmptyState` / `AIStatus` / `SourceItem` 与统一 class 常量，消除各页重复的局部常量（6 组降至 2 组）。
- 记录页与时间线页分离：记录页 = PageHeader + Capture Composer + `RecentEntries`（最多 8 条、无筛选器）；时间线页 = `FilterBar` + 日期分隔 + 完整分页。
- Entry 一级视图只显示总状态（处理中 / 已整理 / 需复核 / 失败）；逐项 AI 状态与 Metadata 表单移入 AI 详情 Drawer；更多菜单新增「查看历史」，接入既有 `GET /entries/{id}/versions` 与 `/versions/{n}/diff`（只读，未接 restore）。
- 搜索页三态：未搜索（最近搜索 + 保存的搜索 + 知识对象）、有结果（命中类型徽标）、空结果（`EmptyState` + 可操作建议）。
- 问记忆三态：未提问（示例问题 + 最近提问）、回答（对话列 + Sources 一级栏 + 追问入口）、移动端 Sources Bottom Sheet。
- 新增 `web/src/lib/recent-activity.ts`：localStorage 记录最近搜索 / 最近提问，无后端变更。

验证：`npm run build` 通过；`pytest` 50 passed；`ruff` All checks passed；`scripts/smoke.sh` passed；`tests/playwright_smoke.py` passed；390×844 与 430×932 四页横向溢出均为 0；硬编码颜色与 Tailwind 调色板扫描均为 0。

已知限制：`ask` 为单轮无状态（追问 = 新提问）；最近搜索/提问仅存本机；无「常用来源」模块（后端无接口，未用假数据填充）；iOS Safe Area 与 Dark Mode 未逐页截图验证。详见 `docs/ui/STARMEM_UI_V2_COMPLETION.md`。

### 2.3 全站 UI Composition 重构（2026-09-16，历史记录）

以下记录对应用户最新 Tabler 要求之前的 Preline Composition 阶段；当前结果以 2.4 及 `docs/ui/STARMEM_TABLER_MIGRATION_REPORT.md` 为准。

用户确认执行全站页面级 Preline Composition Audit 与重构；change：`starmem-full-site-composition`。已枚举 23 个用户可访问 Route/嵌套路由表面，全部映射到 Capture、Browse、Search、AI、Detail、Management 六类母版并标记 `completed`。

关键改动：

- 统一 Application Shell：分组 Sidebar、桌面 Header、移动 off-canvas、五项 Bottom Navigation、正式 Logo；保留原图 `assets/starmenlogo.png`，使用时通过透明边界裁剪后的 `web/public/starmem-logo.png`。
- 统一 `PageFrame`、`SectionHeader`、`LoadingState`、`ErrorState`、`EmptyState`、`DetailRail`、`ManagementNav`，并将 Record、Timeline、Search、Ask、Inbox、Workbench、Sources、Settings、Models、Prompt、AI Jobs、Memory、Entry Detail、History、404 全部接入页面级 Composition。
- Prompt Studio 拆为 Prompt List/Editor、Version History、Test Cases；AI Jobs、Memory、Entry、Job、Source 均提供真实数据驱动的列表/详情路径；未虚构 Connector、Dashboard KPI 或同步状态。
- 新增 `docs/ui/STARMEM_PAGE_INVENTORY.md`、`docs/ui/STARMEM_FULL_SITE_UI_AUDIT.md`、`docs/ui/UI_COMPOSITION_RULES.md`、`docs/ui/PRELINE_SOURCE_MAP.md` 与最终报告；固定 Preline commit 为 `05ca59998db345cfede649b00093032409b37f25`。

验证：`npm run build`、`docker compose build web`、API pytest（50 passed）、ruff check、集成 smoke、Playwright smoke/traversal、Composition QA（25 routes、6 viewports、dark mode）均按实际记录完成；`openspec validate --all --strict` 为 30 passed / 0 failed。`ruff format --check` 当前仅剩既有 `backend/app/providers.py:323` 格式问题，本次 UI 变更未触碰该文件。长序列浏览器验收使用临时 1000 req/min override，完成后已恢复产品默认 120 req/min。

### 2.4 UI Tabler 严格模板迁移（2026-09-16）

用户最新要求已将视觉 Source of Truth 从历史 Preline 迁移为 pinned Tabler 官方源码；本节是当前 UI 状态，旧的 Preline UI 记录仅作为历史交接，不再作为新页面实施依据。change：`starmem-tabler-migration`，OpenSpec 任务 30/30 完成。

实际完成：

- clone 并构建 `.reference/tabler`，commit `0776b88863690c9740d7d33988a8b5df66aad6dc`，version `1.5.1`；官方 Preview 已启动并保存 9 张参考截图。
- vendor 官方 `tabler.css`、`tabler-vendors.css`、Dropzone CSS、Tabler ESM/theme JS；所有 vendor 文件与 pinned build 逐一一致并记录 SHA-256。
- 全部 23 个用户可访问 Route/逻辑页面完成六类母版归类、Tabler Source Mapping、Shell/页面 Composition、Empty/Loading/Error/Loaded 状态和 Inventory `completed`。
- 移除生产前端的 Preline/Lucide/Tailwind 视觉依赖，统一使用 Tabler/Bootstrap class 与 `@tabler/icons-react`；保留原始 Logo `assets/starmenlogo.png`，运行时使用裁剪透明边界版本 `web/public/starmem-logo.png`。
- 最终截图位于 `docs/ui/screenshots/tabler/`，包含 37 张桌面/移动截图（含 1920 宽屏）；完整结果见 `docs/ui/STARMEM_TABLER_MIGRATION_REPORT.md`。

验证（实际运行）：`pytest -q` 为 50 passed；`ruff check` 通过；`npm run lint`、`npm run build`、`docker compose build web`、`scripts/smoke.sh`、Playwright smoke/traversal、Composition QA（25 routes × 6 viewports + dark mode）均通过；`curl /health` 显示 database/redis true。长序列浏览器验证使用临时 1000 req/min override，完成后已删除并恢复默认 `120 req/min`。

已知限制：`ruff format --check` 仍被迁移前就存在的 `backend/app/providers.py:323` 阻断，本次未修改该后端文件；真实 iOS Safari 硬件安装验收未执行；Vite 仅报告官方 Tabler/图标 bundle 大于 500 kB 的 warning，不影响构建和运行。详细偏差见 `docs/ui/TABLER_DEVIATIONS.md`。

### 2.5 UI Tabler Typography 一致性与自动校验（2026-09-16）

用户确认执行字体体系修复与自动视觉校验；change：`starmem-tabler-typography`，OpenSpec 任务 14/14 完成。

实际完成：

- 基于 pinned Tabler `0776b88863690c9740d7d33988a8b5df66aad6dc`（1.5.1）核对真实 Typography 源码；确认官方使用系统 sans/monospace stack、无 Inter Web Font，并记录到 `docs/ui/TABLER_TYPOGRAPHY_AUDIT.md`。
- StarMem 仅在官方 sans stack 后追加 `Noto Sans SC`、`Microsoft YaHei UI`、`Microsoft YaHei` CJK fallback；字号、字重、行高、字距、font-feature-settings、monospace 和页面布局均未改动。偏差记录在 `docs/ui/TABLER_DEVIATIONS.md`。
- 新增隐藏的 `/__ui/tabler-typography-fixture`，由双方共用的 deterministic Tabler DOM/class fixture 驱动；未加入正常导航或业务页面。
- 新增 `scripts/ui/validate-tabler-typography.mjs` 与 `scripts/ui/audit-page-typography.mjs`：覆盖 CDP 实际渲染字体、computed style、Bounding Box、pixelmatch 截图、font network、console、overflow、light/dark 及 4 个 viewport。
- `npm run ui:validate-tabler` 实测通过 8/8 Fixture 组合与 40/40 真实页面组合；截图差异最高约 0.0027%，固定门槛为 0.1%。完整 artifacts 位于 `artifacts/ui/`，最终报告为 `docs/ui/STARMEM_TABLER_TYPOGRAPHY_REPORT.md`。

验证：`npm run lint`、`npm run build`、Docker Web build、API pytest（50 passed）、ruff check、`scripts/smoke.sh`、Playwright smoke、traversal、Composition QA（25 routes × 6 viewport、dark mode）均按实际记录通过；`openspec validate --all --strict` 为 32 passed / 0 failed。Typography 与长序列浏览器审计使用临时 1000 req/min QA override，结束后已删除并确认服务恢复产品默认 120 req/min。`ruff format --check` 仍仅剩既有 `backend/app/providers.py:323` 格式问题；真实 iOS Safari 硬件验收未执行。

### 2.6 UI Tabler 字体真实生效验证（2026-09-16，历史阶段）

本节记录移除自定义 CJK fallback 之前的中间状态；当前字体约束与结果以 2.7 节为准。

用户确认执行严格的 Chromium 实际 Rendered Fonts 校验；change：`starmem-tabler-font-verification`，OpenSpec 任务 12/12 完成。

实际完成：

- 复用 pinned Tabler Reference 与生产 Typography Fixture，新增不进入导航的 `/__ui/tabler-font-fixture` 入口；固定样本覆盖 Latin、Search、Settings、Import Inbox、数字、UUID、技术字符串、CJK、混排、Button、Input、Select、Badge、Status、Table、Link、Code 和 Pre。
- 新增 `scripts/ui/verify-tabler-rendered-fonts.mjs`，使用 Playwright + Chromium CDP `CSS.getPlatformFontsForNode` 逐节点采集 Reference/StarMem 实际字体，并生成 `artifacts/ui/fonts/` 下的独立 JSON/PNG/Diff 证据。
- 扩展真实页面字体审计输出 `artifacts/ui/fonts/real-page-font-audit.json`，增加 `ui:verify-fonts`、`ui:audit-fonts`、`ui:verify-tabler-fonts`；保留原 `ui:validate-tabler` 兼容命令。
- 发现并修正一次真实页面审计的语义误报：`button.status` 使用与 Reference 同 DOM 语义的官方节点进行比较；未修改生产布局或放宽字体规则。最终 18/18 节点、8/8 Fixture 组合、40/40 真实页面组合通过。

验证：`npm run ui:verify-tabler-fonts`、`npm run ui:validate-tabler`、Web lint/build、Docker Web build、API pytest 重跑（50 passed）、ruff check、集成 smoke、Playwright smoke/traversal、Composition QA（25 routes × 6 viewport、dark mode）均通过；`openspec validate --all --strict` 为 33 passed / 0 failed。验证期间临时 QA 限流 override 已删除，服务恢复产品默认 120 req/min。完整证据与限制见 `docs/ui/STARMEM_TABLER_FONT_VERIFICATION_REPORT.md`；`ruff format --check` 的既有 `backend/app/providers.py:323` 问题和真实 iOS Safari 硬件未验收保持记录。

### 2.7 UI Tabler 官方字体栈收敛（2026-09-16）

用户进一步确认“完全继承 Tabler 官方字体栈、移除自定义 CJK fallback”。已删除 `web/src/styles.css` 中的 `--tblr-font-sans-serif` 追加规则，保持 Tabler vendor CSS 原样；所有字体校验器改为 CJK 与 Reference 的实际 platform font 严格一致。由于官方 Preview 初始 `lang=en` 会在中文节点首次 shaping 后固定 JP fallback，校验器在注入 Fixture 前统一为 `zh-CN`，这是测试条件对齐，不是生产字体覆盖。

最终 CDP 结果：Latin/数字/UUID/技术字符串为 `Noto Sans`，CJK Reference/StarMem 均为 `Noto Sans CJK SC`，monospace 均为 `Liberation Mono`；8/8 Fixture、18/18 节点、40/40 真实页面通过，Screenshot Diff 为 0%。本次未修改布局、页面 Composition、业务逻辑或 Tabler vendor CSS；服务已恢复默认 120 req/min。

### 2.1 Chat provider 兼容性修复（2026-09-16，无 OpenSpec change）

用户确认将 Chat 切到自建节点：lstable（Tesla V100-PCIE-16GB）上的 llama.cpp + Qwen3.5-4B，经 `https://llm.soocoo.xyz/v1` 暴露（该容器未发布端口，仅经入口访问）。

接通后 summarize / relation_build / Ask 回答 / Prompt Studio Draft 测试全部 HTTP 500，服务端日志为 `Jinja Exception: No user query found in messages.`。根因：Qwen3.5 官方 chat template（llama.cpp `--jinja`）要求 messages 必须含 `user` 消息，而这三处调用只发送了 `system`；此前 Chat 未配置、请求未发出，故未暴露。注意 classification / tag / entity_extract / time_extract 显示成功是走了 `_run_deterministic` 本地规则，并未调用模型。

修复（仅后端，未改 Prompt 正文与输出 Schema）：

- `backend/app/providers.py` 新增 `task_messages()`：按 OpenAI Chat 协议构造 `[system(指令), user(触发)]`。
- `backend/app/ai_tasks.py`（summarize / relation_build）、`backend/app/ask.py`、`backend/app/prompting.py`（Draft 测试）改用该 helper；Ask 使用贴合语义的 user 文案。
- `backend/tests/test_ask.py` 增加 `_offline_chat()`，使单测不再依赖外部 Chat 配置（此前 `.env` 加了 Chat 配置后 `chat_available=True`，会走到 `resolve_prompt(db=None)` 而失败）。

配置：`.env` 增加非敏感项 `STARMEM_CHAT_BASE_URL=https://llm.soocoo.xyz/v1`、`STARMEM_CHAT_MODEL=qwen35-4b`；API Key 由部署者填写（`.env` 已被 `.gitignore` 忽略，未提交）。

验证：`pytest` 50 passed；`ruff` 通过；重建 api/worker 后对一条 Entry 触发「重新 AI 处理」，8 个 Job 全部 `done`（含此前失败的 summarize / relation_build）；Ask 返回 LLM 生成答案而非确定性摘要降级。Embedding 保持本地 `fastembed / BAAI/bge-small-zh-v1.5`。

### 2.2 检索相关性修复（2026-09-16，无 OpenSpec change）

用户报告「问记忆」查询 `创建云盘命令` 时列出无关来源（`你好你好`、`撒地方`）。根因有三：语义检索无相似度阈值只做 top-k；混合评分按相对最高分归一化，把 0.32 的相关度放大到 0.55 并让置信度虚高为 45%；中文查询被整体当作单个 token，关键词通道实际失效。

已修复（范围经用户确认）：

- 新增配置 `STARMEM_SEMANTIC_MIN_SIMILARITY`（默认 `0.35`）：既无关键词字面命中、语义相似度又低于阈值的候选直接丢弃。
- 混合评分改用绝对分数（语义分量用真实余弦值），移除按最高分归一化的放大效应。
- 新增中文 bigram 查询切分（零新依赖）并逐 token 执行 `ilike`，同时转义 LIKE 通配符，恢复中文关键词召回。
- `AskOut` / `SearchOut` 新增 `filtered_low_relevance`，问记忆与搜索页在发生过滤时提示「已过滤 N 条低相关结果」。
- 影响面：`/api/v1/ask`、`/api/v1/search` 及 Workbench 已保存搜索的结果数与置信度会一并变化。

验证：`docker compose up -d --build` 后 `/health` ok；`pytest -q` 50 passed；`ruff check` 与 `ruff format --check` 通过；`scripts/smoke.sh` passed；`tests/playwright_smoke.py` passed。真实数据端到端：查询 `创建云盘命令` 由 3 条来源 / 置信度 45% 变为 1 条来源（`openstack volume create`）/ 置信度 26%、`filtered_low_relevance=2`；无关查询 `完全不相关的外星词汇zzz` 返回 0 条、`filtered_low_relevance=3`；UI 实测显示过滤提示与 1 张来源卡片。

## 3. 已实现能力

### 3.1 P0 基础层

- Docker Compose：Web、FastAPI API、Dramatiq Worker、PostgreSQL/pgvector/pg_trgm、Redis。
- Raw Capture/Timeline：事务性 Entry、EntryVersion、初始 ContentUnit、独立 AI Job、cursor 分页、日期过滤、Pin/Favorite、编辑、Diff/Restore、软删除。
- Search：PostgreSQL FTS、trigram/ILIKE、FastEmbed 语义检索和 Hybrid；技术标识符精确命中优先。
- Source/Provenance：`StarMem Native`、ExternalItem/ContentUnit 外部快照边界、Chunk/Memory 来源追溯。
- AI/Prompt：可替换 Chat/Embedding/Reranker Provider、独立 Job、规则提取、Prompt Registry、Draft/Testing/Production、严格输出 Schema、失败隔离。
- Memory：Observation、Memory Candidate、Canonical Memory、Salience、Retrieve-Before-Write、有限 Reconcile 操作、scope 锁、SUPPORT/SUPERSEDE/CONFLICT 等生命周期。
- Ask：Query Understanding、时间提示、Hybrid/Memory 上下文、来源引用、无来源拒答、事实/推断标识和原文跳转。
- Web/PWA：桌面侧栏、移动五项导航、Safe Area、草稿恢复、manifest、Service Worker、设置/Prompt Studio/Job/Memory 页面。
- 运维：结构化 secret-safe 日志和指标、备份/显式确认恢复、Embedding 重建、集成 smoke。

### 3.2 P1 输入与 Ingestion

对应 `backend/app/services/ingestion.py`、`backend/app/services/import_parsers.py`、`backend/app/storage.py` 和 `backend/app/models.py` 的 Attachment/IngestionJob 能力：

- URL 安全抓取：HTTP/HTTPS、大小/超时/重定向/内容类型限制、DNS/IP SSRF 防护、标题和正文快照。
- 文件：TXT、Markdown、JSON、YAML、Log、PDF、图片；统一进入 Native Entry 和 Inbox。
- PDF 页级 ContentUnit、页码保留、扫描页 OCR；本地 Tesseract OCR，不走远程 Chat。
- Attachment 使用 UUID 存储键、SHA-256 完整性校验、原始文件名不直接作为路径。
- Idempotency-Key、处理状态、attempt 锁、失败码、可安全 retry，不重复创建 Entry/Attachment/ContentUnit。
- Inbox 列表/详情/状态过滤/重试，Search/Ask provenance 保留 attachment/page 信息。

### 3.3 P1 Knowledge Workbench

- Project/Topic/Entity 列表和详情：首次/最近出现、Entry/Memory 数量、来源 ID、相关对象。
- Saved Search：查询、来源范围和过滤器持久化，结果按当前数据重新执行，不保存结果快照。
- Smart View：问题、解决方案、TODO、决策、测试/性能、最近修改、未解决、新/冲突 Memory、失败 AI Job。
- Daily/Weekly/Monthly Review：有界统计和可跳转来源。
- Deterministic Knowledge Summary：保留 `entry_ids`/`memory_ids` provenance，不替代 Atomic Memory。
- 本地 Secret Scanner：只保存类型、行列、内容 hash、扫描版本和时间，不保存匹配值；支持重扫。
- Advisory Similar Entry：pg_trgm 优先，本地有界相似度 fallback；只建议，不自动覆盖/合并/删除。
- 任务模型路由：Prompt Version 路由优先于用户路由，最后回退全局运行时 Chat；响应只返回 provider/model，不返回凭据。

### 3.4 P1 Mobile Share Target

- `web/public/manifest.webmanifest` 注册同源 `POST /share` multipart Share Target，接受 title/text/url 和文本、图片、PDF 等文件。
- `web/public/sw.js` 将最近一次分享写入 IndexedDB `starmem-share`，限制总大小 20 MiB、最多 4 个文件；读取后删除，不写入 Cache Storage。
- Capture 根据 `?shared=1` 预填文本、URL 或内存 File；文本附带 URL 时可切换为网页 URL；错误显示可理解反馈。
- 分享后的保存继续复用 `/entries`、`/ingest/url`、`/ingest/file`，因此沿用 CSRF、SSRF、上传大小、OCR、附件哈希和 Inbox 边界。
- 真实 iOS/Android 系统分享菜单和 Safari Home Screen 仍需要真机验收，当前只有 Chromium 浏览器验收。

### 3.5 P1 Native Portability

- `GET /api/v1/export?format=json|jsonl|markdown|zip&source_scope=all|native|external`：默认排除软删除，最多 10,000 条。
- JSON/JSONL 包含 Raw、内容/时间/来源字段、标签、实体、Observation、active/conflicted Memory 引用和附件元数据。
- Markdown 以 `starmem-entry-id` 注释保留 Entry 回溯关系。
- ZIP 包含 `starmem-export.json` 和经 SHA-256 校验的原始附件，路径为 `attachments/<entry_id>/<attachment_id>-<safe-name>`，下载名为 `starmem-export-YYYYMMDD.zip`。
- `POST /api/v1/import` 仅接受 `.json`/`.jsonl`，支持 `entries` 包装对象、对象数组和 JSONL；最多 100 条并复用上传字节上限。
- 导入按未删除 Entry 的 Raw/title 精确去重，返回 `created_count`、`skipped_count`、`entry_ids`、`errors`；新 Entry 复用 EntryVersion、ContentUnit、AI Job 和本地安全扫描，不覆盖/删除已有数据。
- Web More 页的“数据搬迁”卡片提供四种下载和原生备份文件选择；导入反馈 created/skipped/error。
- ZIP 只实现导出，导入不解包 ZIP、不适配第三方格式、不恢复附件元数据到存储。

### 3.6 P1 设计对齐闭环（parity closure）

- Capture 支持 Ctrl/Cmd+Enter 保存与空内容提示，按钮路径保留。
- Entry 多分类 `content_types`（JSONB，主分类 `content_type` 保留，空集回退主分类）；人工编辑写入用户锁定，AI 重跑不覆盖；按类型检索同时匹配主分类与集合。
- Entry 列表批量返回 `tags` 与 `ai_status_items`，卡片直接显示标签与逐项 AI 状态（索引/Embedding/分类/摘要/标签/实体/时间/项目/主题/Memory/关系/图片描述），失败项可重试。
- Related Entry 确定性信号（共享实体/标签、同 Project/Topic/Error/Host、语义相似度）并返回命中理由。
- 时间线支持自定义起止日期，保留今天/昨天/本周/本月预设。
- 搜索支持全文/语义/混合模式与类型/标签/实体/项目/主题/时间过滤；Saved Search 保存并复用完整过滤器。
- Memory 生命周期闭环：确认、标记 expired（写 `expired_at`/`valid_to`）、删除、状态筛选。
- Prompt Studio：克隆内置 Prompt、编辑 Layer 2 Task Prompt 与 provider/model/temperature/top_p/max_tokens、Preview、Draft 测试、用户自定义 Test Case CRUD（内置用例禁止改删）。

## 4. 关键代码与入口

### 后端

- `backend/app/api.py`：认证、Entry、Ingestion、Search、Ask、Workbench、Export/Import 路由。
- `backend/app/models.py`：核心数据模型；P1 Workbench 增加 `EntrySafetyScan`、`SavedSearch`、`UserSetting.model_routing`。
- `backend/app/schemas.py`：API/Pydantic contract；`EntryCreate.source_uri` 是为原生导入补充的兼容字段。
- `backend/app/services/entries.py`：Raw-first Entry 创建、版本、ContentUnit、AI Job、安全扫描和队列。
- `backend/app/services/ingestion.py`：URL/文件/PDF/OCR/附件异步处理。
- `backend/app/services/portability.py`：原生导入导出、边界、白名单序列化和 ZIP 附件。
- `backend/app/services/workbench.py`、`safety.py`、`secret_scanner.py`：Workbench、扫描、相似建议和 Summary。
- `backend/app/services/related.py`：Related Entry 确定性信号与理由。
- `backend/app/services/curation.py`：Entry 多分类、Metadata 锁定、逐项 AI 状态聚合与批量信号。
- `backend/app/prompting.py`：Prompt 草稿（含 Task Prompt 与模型参数）与内置克隆。
- `backend/app/worker.py`、`ai_tasks.py`、`ask.py`、`routing.py`：派生任务、Ask 和模型路由。
- `backend/alembic/versions/0001_initial_schema.py` 至 `0010_parity_closure.py`：当前迁移序列；最近 head 为 `0010_parity_closure`。

### 前端与测试

- `web/src/main.tsx`：Capture、Timeline、Search、Ask、More、Inbox、Workbench；More 中有数据搬迁入口。
- `web/src/api.ts`：前端 API client，包括 `importNative`。
- `web/src/share.ts`、`web/public/sw.js`、`web/public/manifest.webmanifest`：PWA Share Target。
- `web/src/styles.css`：响应式和可访问交互样式。
- `backend/tests/test_p1_portability.py`：四种导出、附件归档、导入创建/去重/格式拒绝。
- `backend/tests/test_parity_closure.py`：多分类、Related 信号、AI 状态聚合、Chat 未配置时步骤跳过、Memory 生命周期、Prompt 克隆/参数/Test Case、Saved Search 过滤器。
- `tests/playwright_smoke.py`：PWA、Share Target、实际文件分享、响应式、Capture→Search→Ask→Workbench→Inbox、导出下载和导入反馈。
- `tests/playwright_traversal.py`：逐页面遍历关键按钮并断言状态与业务效果（含多分类、日期范围、Memory 生命周期、Prompt Studio）。
- `scripts/smoke.sh`：API/Worker/数据库/队列的集成 smoke。

### 文档与 OpenSpec

- [完整 P0 报告](P0_COMPLETION_REPORT.md)
- [P1 输入与导入](implementation/phase-p1-ingestion.md)
- [P1 Knowledge Workbench](implementation/phase-p1-workbench.md)
- [P1 Mobile Share Target](implementation/phase-p1-mobile-share.md)
- [P1 Native Portability](implementation/phase-p1-portability.md)
- [P1 Gap Closure](implementation/phase-p1-gap-closure.md)
- [P1 设计对齐闭环](implementation/phase-parity-closure.md)
- [本地 Chat/Embedding 配置](LOCAL_LLM.md)
- [备份与运维](BACKUP_AND_OPERATIONS.md)
- OpenSpec 主 spec：`openspec/specs/`（已由归档 change 同步）。
- OpenSpec archive：`openspec/changes/archive/2026-09-15-*`；P0 与 4 个 P1 change 已归档。

注意：`docs/P0_COMPLETION_REPORT.md` 是 P0 时点报告，其中“P1 附件/OCR 未实现”是历史截面；当前事实应以 P1 输入实施记录和代码为准。

## 5. 当前运行环境与模型

### Compose

当前容器均为 running：

- Web：`http://localhost:18780`
- API：`http://localhost:18000`
- PostgreSQL：Compose 内部 5432
- Redis：Compose 内部 6379
- Worker：Dramatiq

最近状态检查：

```json
{
  "health": {"status": "ok", "database": true, "redis": true},
  "chat_configured": false,
  "chat_model": "qwen35-4b",
  "embedding_provider": "fastembed",
  "embedding_model": "BAAI/bge-small-zh-v1.5"
}
```

当前工作区没有 `.env`，所以状态接口显示 `chat_configured=false` 是预期结果，不表示 Chat Provider 代码不可用。

### Chat 与 Embedding

- 已验证 OpenAI-compatible Base URL：`https://llm.soocoo.xyz/v1`。
- 已验证 Chat model：`qwen35-4b`。
- Chat 请求默认带 `chat_template_kwargs.enable_thinking=false`。
- `/v1/models` 可见 `qwen35-4b`；Chat 请求曾返回 200。
- 该服务的 `/v1/embeddings` 曾返回 501，因此语义索引使用独立本地 FastEmbed `BAAI/bge-small-zh-v1.5`，维度 512。
- API Key 只允许通过未跟踪 `.env` 或运行时环境注入；本交接文档、代码、镜像、日志和前端不得包含具体 Key。
- 配置说明见 [`docs/LOCAL_LLM.md`](LOCAL_LLM.md)。

## 6. 最终验证结果

以下结果对应当前最终代码；警告是 FastAPI/Starlette/httpx 的弃用提示，不是测试失败：

```text
docker compose exec -T api pytest -q tests/test_p1_portability.py
1 passed, 3 warnings

docker compose exec -T api pytest -q
50 passed, 8 warnings

docker compose exec -T api ruff check app tests alembic
All checks passed!

docker compose exec -T api ruff format --check app tests alembic
pre-existing failure: backend/app/providers.py:323

docker compose exec -T api alembic current
0010_parity_closure (head)

docker compose build web
TypeScript/Vite build passed

scripts/smoke.sh
integration-smoke: passed

python3 tests/playwright_smoke.py
playwright-smoke: passed

python3 tests/playwright_traversal.py
playwright-traversal: passed

openspec validate --all --strict
33 passed, 0 failed
python3 tests/playwright_composition.py
playwright-composition: passed (25 routes; 6 viewports; dark mode)
python scripts/benchmark.py --entries 2000 --embedding-entries 200 --samples 20
raw_save p50 4.64ms / fts p50 82.10ms / hybrid p50 107.09ms / ask_local p50 26.97ms

curl http://localhost:18000/health
database/redis true
```

浏览器验收实际覆盖：登录、manifest、Service Worker Share Target、文本/URL/文件分享、响应式 375/768/1024/1440、More 页 JSON 下载、原生 JSON 文件选择、重复导入 `created=0/skipped=1`、Capture→Search→Ask→Workbench→Inbox；遍历测试覆盖 Capture 键盘保存、Entry 多分类与逐项 AI 状态、Related 理由、时间线日期范围、搜索模式与 Saved Search 过滤器还原、Memory 生命周期、Prompt Studio 克隆/参数/预览/Test Case。测试生成的 Entry、Memory、Saved Search、Prompt Draft 与自定义 Test Case 已删除；工作区缓存和临时产物已清理。

页面执行错误排查已修复：Workbench 切换类型标签时的详情 404（`selectedId` 跨类型残留）；并移除了会导致 429 的每卡片 tags/ai-status 请求。全页面交互（含 AI 步骤重试）在 console error / pageerror / HTTP>=400 上为 0。

遍历测试请求量高于默认限流，验证时通过临时 Compose override 提高 `STARMEM_RATE_LIMIT_PER_MINUTE` 后运行，验证后已恢复默认值（产品默认限流未改动）。

## 7. 后续接续规则

### 继续开发前

1. 先读根目录 `AGENTS.md`、本文件、README 和相关 OpenSpec；用户此前要求的五份完整文档已读，但需求发生变化时仍需重新核对相关章节。
2. 检查 `openspec/changes/`、容器状态、迁移 head 和工作区已有改动；不要覆盖其他协作者的修改。
3. 已完成范围不要重复实现：尤其是 `0008_p1_workbench`、Ingestion、Share Target 和 Native Portability。
4. 新增用户可见行为、公共 API、schema、数据迁移、依赖或跨层能力时，先做完整 Requirement Review；需要时使用 OpenSpec Propose/Apply。
5. 不以 `tasks.md` 全勾选替代运行验证；修改后必须按真实用户路径重新测试并记录实际结果。

### 当前候选工作（均需新的范围确认）

这些不是当前已授权的实现项，只是路线入口：

- P1 Gap Closure 已交付：Relation 读取、Metadata 人工编辑与锁定、Project/Topic/Entity 管理、Inbox 修正、图片描述降级、批量重处理、Reranker、Ask 日志与「最近常问」；不要再重复实现。
- P1 设计对齐闭环已交付：Capture 键盘保存、Entry 多分类与逐项 AI 状态、Related 确定性理由、时间线日期范围、搜索模式与过滤器、Saved Search 过滤器、Memory 生命周期、Prompt Studio 克隆/参数/Test Case；不要再重复实现。
- P1 后置：External Corpus Connector、CLI、MCP、浏览器插件、多人/RBAC、P1 高级 Prompt 克隆/编辑。
- P2：Knowledge Graph/Relation Graph UI、Topic/Project Evolution、Advanced Memory Consolidation、自动知识归并、主动提醒、Agent 主动读取 Memory、多源同步、邮件/IM/GitHub/Calendar ingestion、每日/每周总结、Memory Quality Score、Knowledge Gap Detection、Long-term Trend Analysis、Personal Knowledge Synthesis。
- 真机验收：iOS Safari/Home Screen 安装、系统分享菜单、键盘、网络切换和 Safe Area。

若用户没有重新确认，不要因为这些能力出现在原始产品文档中就开始实现。优先保持单体 Compose、Native Source、Source/ContentUnit/Provenance 和现有 Raw-first contract 稳定。

## 8. 已知限制与风险

- 当前是单用户系统，没有多人隔离和 RBAC；不要把现有 API 当作团队权限边界。
- Chat 当前运行状态未配置 Key；已验证配置路径和 Provider contract，但最终环境未宣称真实远程答案质量通过。
- 本地 Embedding 首次加载会有下载延迟，模型缓存依赖 Compose volume。
- Share Target 依赖已安装/启用 PWA 和 Service Worker，多文件只恢复第一个到 Capture。
- Native Portability 导入只接受 StarMem 原生 JSON/JSONL；第三方格式和 ZIP 反向导入不支持。
- 导出是有界快照：最多 10,000 条；导入最多 100 条并受上传字节限制。
- 安全扫描是本地提示，不阻断保存；远程 Chat 仍需使用现有 `redact_secrets` 防线。
- 逐项 AI 状态依赖已创建的 AI Job；未配置 Chat Provider 时 Chat 依赖步骤标记为 `skipped`（`provider_not_configured`）并显示“已跳过（未配置）”，不再显示为失败；配置 Chat 后重新处理即可执行。真正请求失败的步骤仍显示失败并可重试，不影响原文保存。
- Related 信号为有界多次查询，候选数量受限，不保证穷举。
- 检索相关性阈值 `STARMEM_SEMANTIC_MIN_SIMILARITY` 默认 0.35，需按 embedding 模型和语料调整：过低会重新引入噪音，过高可能漏掉语义偏弱但确实相关的内容；关键词字面命中的候选不受该阈值限制。
- 默认 API 限流为 120 req/min；高速端到端遍历需要临时提高限流，单用户日常使用不受影响。
- 恢复脚本会覆盖目标数据库/附件 volume，属于显式确认后的破坏性操作；未在当前数据上执行恢复。

## 9. 推荐接续命令

```bash
cd /home/superc/code/starmem
docker compose ps
curl http://localhost:18000/health
docker compose exec -T api alembic current
docker compose exec -T api pytest -q
docker compose build web
scripts/smoke.sh
```

涉及浏览器行为时，再执行：

```bash
STARMEM_TEST_EMAIL=admin@starmem.local \
STARMEM_TEST_PASSWORD=change-this-password \
python3 tests/playwright_smoke.py
```

测试完成后必须删除明确的测试数据，检查 `.env`、Key、缓存和临时文件没有进入交付范围；不要执行 `git reset --hard`、`git clean` 或未经授权的 commit/push。
