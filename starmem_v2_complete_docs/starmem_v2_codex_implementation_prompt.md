# Codex 实施提示词：StarMem v2

你是一名高级全栈工程师、AI/RAG 工程师和软件架构师。

你的任务不是只给出建议，而是直接完成一个可运行、可测试、可持续演进的 **StarMem**。

你必须以“结果交付”为目标，严格按照本提示词和项目 PRD 实施。

---

## StarMem 品牌命名

项目正式名称：

> **StarMem**

英文副标题：

> **Your Personal AI Memory Repository**

中文定位：

> **零整理成本的个人 AI 记忆仓库。**

核心理念：

> **你负责忘记，StarMem 负责记住。**

统一工程命名：

```text
starmem-web
starmem-api
starmem-worker
starmem-mcp
```

统一 CLI：

```bash
starmem add "..."
starmem search "..."
starmem ask "..."
starmem get <id>
```

统一 MCP Tool 前缀：

```text
starmem_add
starmem_search
starmem_ask
starmem_get
starmem_find_related
```

---


# 0. 必读输入

首先读取并完整理解以下需求文档：

```text
starmem_v2_prd_architecture.md
```

如果该文件位于当前项目目录之外，请根据实际路径寻找它。

该文档是项目的主需求规范。

本提示词用于约束你的开发行为、实施顺序和验收方式。

如本提示词与 PRD 存在细节冲突：

1. 产品功能与数据模型：以 PRD 为准
2. 实施方式与工程纪律：以本提示词为准
3. 不允许因为冲突而跳过实现
4. 应采用最保守、最易维护、最少过度设计的方案

---

# 1. 项目目标

构建一个：

> 零整理成本、可追溯、可长期演化的StarMem。

用户每天可以把大量杂乱文本直接输入系统，不需要先：

- 想标题
- 选目录
- 选项目
- 打标签
- 分类

系统后台自动完成：

- 原始内容保存
- 全文索引
- Chunk
- Embedding
- AI 分类
- AI 摘要
- AI 标签
- Entity 提取
- 时间信息提取
- Project / Topic 识别
- Memory 提取
- Memory 生命周期管理
- Related Entry
- Hybrid Search
- Ask / RAG
- Source Citation
- iOS Responsive Layout
- PWA Manifest
- Safe Area
- Source Attribution
- ContentUnit Search
- Search Scope
- Prompt Version
- Prompt Rollback
- Prompt Schema Validation
- Prompt Golden Dataset
- User Instructions Override
- Salience
- Reconcile ADD
- Reconcile SUPPORT
- Reconcile SUPERSEDE
- Reconcile CONFLICT
- Reconcile MERGE
- Reconcile IGNORE
- Reconcile Concurrency

用户后续应能：

- 按时间查找
- 按关键词查找
- 按 Host / IP / UUID / WWN / Error Code 查找
- 用模糊自然语言找回内容
- 询问历史结论
- 查看结论变化
- 查看 AI 回答引用的原始记录

---


# 移动端与 iOS Home Screen Web App（P0）

StarMem 从项目第一天起就是 **Desktop + Mobile Web 双端产品**。

移动端不是“后续兼容项”，而是正式的一等运行形态。

## P0 必须支持

- iPhone Safari 正常登录和完整使用
- 响应式布局
- 添加到 iOS 主屏幕
- 以独立 Web App / standalone 窗口打开
- `manifest.webmanifest`
- `apple-touch-icon`
- App Icon
- `display: standalone`
- iOS Safe Area：
  - `env(safe-area-inset-top)`
  - `env(safe-area-inset-bottom)`
  - `env(safe-area-inset-left)`
  - `env(safe-area-inset-right)`
- 移动端底部导航
- 输入框、按钮、标签和来源引用全部满足触摸操作
- Markdown / Code Block 不得撑破页面
- 长内容采用单列阅读布局
- Metadata / Entity / Project 等辅助信息在移动端采用 Drawer / Sheet / Collapse
- Capture 草稿自动保存
- 页面刷新、切后台、短暂断网时尽可能不丢失正在输入的草稿
- 登录状态长期保持
- 认证优先采用 HttpOnly + Secure + SameSite Cookie / Session Cookie
- 不把核心登录 Token 只存在 localStorage
- Service Worker 架构预留

## 推荐移动端导航

```text
记录
时间线
搜索
问记忆
更多
```

## 目标体验

用户在 iPhone 上：

```text
Safari
  ↓
打开 StarMem
  ↓
添加到主屏幕
  ↓
点击 StarMem Icon
  ↓
独立 Web App 窗口
  ↓
保持登录
  ↓
快速 Capture / Search / Ask
```

## P1 移动端能力

- 离线查看最近记录
- 离线新建 Entry，恢复网络后同步
- Web Push
- App Badge
- iOS Share Target / 分享到 StarMem
- 网页分享
- 图片分享
- 相机拍照记录
- 语音快速记录
- Passkey / Face ID

其中：

> “从 iOS 分享网页 / 文本 / 图片到 StarMem”属于 P1 高优先级。



# External Corpus：外部大规模文本语料库架构（P0 预留，P1+ 实现）

StarMem 从架构设计阶段就必须假设：

> 未来可能接入几十万乃至更多来自外部系统、历史文本库、工单库、文档库、聊天记录、日志库、知识库的数据。

P0 **不要求实现任何具体 Connector**，但核心数据模型、检索层、来源追踪和 Ingestion Pipeline 必须预留。

## 两类数据来源

```text
StarMem
│
├── Native Content
│   ├── Web
│   ├── iOS
│   ├── CLI
│   └── MCP
│
└── External Corpus
    ├── 文本库
    ├── 文档系统
    ├── 工单系统
    ├── 历史聊天
    ├── 日志库
    ├── Git 仓库文档
    └── 自定义数据源
```

## Source Layer

禁止在 Entry 表中不断添加特定外部系统字段。

必须设计通用 Source：

```text
sources
-------
id
name
source_type
description
config_json
created_at
updated_at
```

建议 source_type：

```text
native
external_api
filesystem
database
http
custom
```

## External Item

外部对象统一抽象：

```text
external_items
--------------
id
source_id
external_id
external_parent_id
item_type
title
raw_content
external_created_at
external_updated_at
content_hash
metadata_json
last_synced_at
created_at
updated_at
```

item_type 可以是：

```text
document
ticket
comment
message
article
page
thread
record
log
wiki
custom
```

## ContentUnit

必须预留统一的最小检索单位：

```text
ContentUnit
```

它可以来自：

- Native Entry
- External Document
- Comment
- Message
- PDF Page
- Log Block
- Code Block
- Web Page Section

建议字段：

```text
id
owner_type
owner_id
unit_type
content
sequence
event_time
created_at
metadata_json
fts_vector
embedding
```

Search Layer 应尽量面向 `ContentUnit`，而不是只面向 Native Entry。

## Provenance / 来源追踪

任何 Search / Ask 结果都必须知道：

- 来源 Source
- External Item
- 原始 ID
- 原始 URL（如果存在）
- 原始时间
- StarMem 导入时间
- 命中的 ContentUnit
- 原始证据片段

## 外部内容默认只读

StarMem 可以：

- 建索引
- Chunk
- Embedding
- Summary
- Entity
- Relation
- Memory
- Knowledge

但不能擅自修改外部原始内容。

External Raw Content 被视为：

> Imported Snapshot / Source Evidence

## 大规模 Ingestion Pipeline

未来外部导入必须采用异步 Pipeline：

```text
Ingestion Job
   ↓
Discover
   ↓
Fetch
   ↓
Normalize
   ↓
Persist Raw
   ↓
Split ContentUnit
   ↓
FTS
   ↓
Embedding
   ↓
AI Processing
```

必须预留：

- `external_id`
- `external_updated_at`
- `content_hash`
- `sync_cursor`
- `last_synced_at`
- Job 状态与重试
- 幂等
- 增量同步

## Import Adapter 接口

P0 只定义接口，不实现具体 Connector：

```python
class ExternalSourceAdapter:
    def discover(self, cursor=None):
        ...

    def fetch_item(self, external_id):
        ...

    def normalize(self, raw_item):
        ...

    def get_cursor(self):
        ...
```

## 搜索范围

架构必须支持：

```text
全部
仅我的记录
仅外部知识库
指定 Source
```

即 Search / Ask 都支持 source scope。

## P0 需要真正做的部分

- Source 基础模型
- `StarMem Native` 内置 Source
- Provenance 统一字段
- ContentUnit 抽象
- Search Scope Filter
- MemorySource 可指向 Native / External Evidence
- Ingestion Job 基础状态模型

## P0 不需要真正实现

- 任意具体外部 Connector
- 外部 API 同步
- 文件系统大批量导入
- 数据库导入
- Webhook
- Incremental Sync UI

但未来增加这些能力时：

> 不允许要求重构 StarMem 核心检索和 Memory 架构。



# StarMem Memory Engine

StarMem 的核心智能层必须设计为：

> 可版本化 Prompt + 结构化 Schema + 可测试 Memory Pipeline + 确定性数据库状态机。

禁止简单实现为：

```text
新内容
↓
把相关旧内容一起丢给 LLM
↓
“请总结并更新记忆”
↓
直接保存模型自由文本
```

## 四层知识模型

```text
┌─────────────────────────────────┐
│ Layer 1 · Evidence              │
│ 用户原文 / 外部原始文本          │
│ 永远不被 AI 修改                 │
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│ Layer 2 · Observation           │
│ Chunk / Entity / Tag / Event    │
│ 问题 / 结论 / 命令 / 配置        │
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│ Layer 3 · Canonical Memory      │
│ 稳定事实 / 当前配置 / 决策 / 结论 │
│ 有生命周期和历史                 │
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│ Layer 4 · Knowledge             │
│ 多条 Memory 综合形成的经验知识    │
└─────────────────────────────────┘
```

原则：

- Evidence 永远不可由 AI 改写
- Observation 可以重新生成
- Memory 可以演化，但必须保留历史
- Knowledge 属于 Derived Data，可以重建

## 新内容处理 Pipeline

```text
New Raw Content
      │
      ▼
① Save Evidence
      │
      ▼
② Deterministic Parse
      │
      ├─ IP
      ├─ UUID
      ├─ WWN
      ├─ hostname
      ├─ date/time
      └─ code block
      │
      ▼
③ AI Observation Extract
      │
      ▼
④ Memory Candidate Extract
      │
      ▼
⑤ Salience Evaluation
      │
      ├─ durable
      ├─ episodic
      └─ ignore
      │
      ▼
⑥ Retrieve Existing Memories
      │
      ▼
⑦ Memory Reconcile
      │
      ├─ ADD
      ├─ SUPPORT
      ├─ SUPERSEDE
      ├─ CONFLICT
      ├─ MERGE
      └─ IGNORE
      │
      ▼
⑧ Deterministic Validator
      │
      ▼
⑨ DB Transaction
      │
      ▼
⑩ Relation / Knowledge Update
```

## LLM 不直接写数据库

LLM 只能输出“建议操作”：

```json
{
  "operation": "SUPERSEDE",
  "target_memory_id": "mem_128",
  "candidate": {
    "subject": "V100",
    "predicate": "power_limit",
    "value": "150W"
  },
  "confidence": 0.98,
  "reason": "新内容明确表示最终配置更新"
}
```

StarMem 程序负责：

- Schema Validation
- 数据存在性检查
- 权限 / 状态检查
- 并发控制
- Transaction
- Unique Constraint
- 最终 DB Apply

## Memory Extract 与 Memory Reconcile 必须分离

### Extract

只回答：

> 新内容说了什么？

### Reconcile

只回答：

> 新事实与已有 Memory 是什么关系？

这是两个不同职责。

## Memory Reconcile 允许的 Operation

```text
ADD
SUPPORT
SUPERSEDE
CONFLICT
MERGE
IGNORE
```

禁止模型返回任意自由数据库操作。

## Salience

必须判断“值得长期记忆”还是“一次性事件”。

例如：

```text
V100 最终以后固定 150W。
```

应属于 durable。

而：

```text
刚才临时测试 175W。
```

应属于 episodic，不得覆盖当前配置。

建议 Memory Candidate 包含：

```text
memory_type
salience
durable
confidence
```

## Retrieve-Before-Write

新 Candidate 不能直接写入。

必须先根据：

- subject exact match
- predicate normalization
- entity
- semantic similarity
- temporal relation

查找现有 Memory。

## 并发写入保护

同一个 Memory Scope，例如：

```text
V100:power_limit
```

必须避免多个 Worker 同时 Reconcile 产生重复 Memory。

建议：

1. Reconcile Queue 按 scope key 串行化
2. DB transaction
3. unique constraint
4. optimistic version / compare-and-swap

## 时间模型

Memory 至少区分：

```text
recorded_at
observed_at
valid_from
valid_to
superseded_at
```

例如：

```text
今天记录：
“上个月开始 V100 就改成 150W 了。”
```

则：

```text
recorded_at = 今天
valid_from = 上个月
```

## Memory Evidence

Memory 必须保留证据来源：

```text
Memory
├── Fact
├── Status
├── Evidence
│   ├── Native Entry
│   ├── External ContentUnit
│   └── Additional Supporting Sources
└── History
```

用户必须能回答：

> 为什么 StarMem 认为这个事实成立？

## Knowledge Consolidation

大量 Atomic Memory 不应该全部合并成一个巨大 Memory。

应形成：

```text
Evidence
   ↓
Atomic Memory
   ↓
Relations
   ↓
Knowledge Summary
```

Knowledge 属于 Derived Data，始终可以追溯到底层 Evidence。



# Prompt Engine / Prompt Studio

StarMem 的 Prompt 必须是正式的一等资源。

Prompt 不允许散落在业务代码中的字符串里。

## Prompt Registry

建议目录：

```text
prompts/
├── observation_extract/
├── entity_extract/
├── temporal_extract/
├── memory_extract/
├── salience_evaluate/
├── memory_reconcile/
├── relation_detect/
├── knowledge_consolidate/
├── query_understand/
└── answer_generate/
```

每个 Prompt 至少具有：

```text
name
version
status
prompt_text
input_schema_version
output_schema_version
model
temperature
top_p
max_tokens
prompt_hash
created_at
created_by
```

状态建议：

```text
Draft
Testing
Production
Archived
```

## Prompt 分层

最终 Prompt 应由四层组成：

```text
Layer 1 · System Safety Contract
Layer 2 · Task Prompt
Layer 3 · User Instructions
Layer 4 · Runtime Context
```

### Layer 1

StarMem 内部保护：

- 不伪造 Evidence
- 必须满足 Schema
- 不允许自由数据库操作
- 不允许把推测当事实
- 不允许静默覆盖历史

普通用户不可直接修改。

### Layer 2

任务 Prompt：

- Memory Extract
- Reconcile
- Ask
- Entity
- Temporal
- Knowledge

默认由 StarMem 提供。

### Layer 3

用户可自由修改的 User Instructions。

例如：

```text
对于技术故障类内容优先提取：

1. 现象
2. 环境
3. 根因
4. 无效尝试
5. 最终解决方案
6. 命令
```

### Layer 4

Runtime Context：

- 当前 Evidence
- Existing Memories
- Entity
- Time Context
- Retrieved Sources

## 用户可修改 Prompt

这是正式产品功能。

设置入口：

```text
设置
  └── AI
       └── Prompt Studio
```

默认模式：

> 用户编辑 `User Instructions`，不破坏系统 Contract。

高级模式：

> Clone Built-in Prompt 后允许完整编辑 Layer 2。

## Schema 与 Prompt 分离

默认：

- Prompt 可修改
- Output Schema 不允许普通模式随意修改

如果模型输出不符合 Schema：

```text
Prompt Validation Failed
```

禁止写入数据库。

高级模式可以修改 Schema，但必须显示高风险警告。

## Prompt Versioning

每次修改：

> 创建新版本，不覆盖历史版本。

例如：

```text
Memory Extract

v1
v2
v3
v4 ← Production
v5 ← Draft
```

必须支持：

- History
- Diff
- Rollback
- Promote to Production
- Restore Default

## Prompt 与模型参数一起版本化

每个版本记录：

- model
- provider
- temperature
- top_p
- max_tokens
- schema version
- prompt hash

## AI 派生结果记录 Prompt Version

每个 Observation / Memory / Knowledge 至少记录：

```text
model
provider
prompt_name
prompt_version
schema_version
generated_at
```

这样未来可：

- 查询某版本 Prompt 生成的全部数据
- 批量 Reprocess
- 对比不同 Prompt 效果

## Prompt Preview

Prompt Studio 必须支持：

```text
Preview Final Prompt
```

显示：

```text
System Contract
+
Task Prompt
+
User Instructions
+
Runtime Context
```

## Prompt Test

用户修改 Draft 后必须能：

```text
[Test Draft]
```

对固定 Test Case 运行。

## Golden Dataset

核心 Prompt 需要固定回归集。

至少包含：

### Memory Extract

- 稳定事实
- 临时状态
- 过去事实
- 当前事实
- 技术日志
- 中英文混合

### Memory Reconcile

- ADD
- SUPPORT
- SUPERSEDE
- CONFLICT
- MERGE
- IGNORE

### Temporal

- 以前
- 现在
- 后来
- 最终
- 去年
- 上个月
- 临时
- 曾经

### Entity

- hostname
- IP
- WWN
- software
- project
- hardware

## 用户自定义 Test Case

用户可以保存自己的回归测试。

例如：

```text
Input:
node-3903 上旧 iscsi session 没有清理，
导致 multipath 出现 undef

Expected:
type=troubleshooting
entities includes node-3903
memory includes root_cause
```

## Prompt 上线流程

```text
Edit
 ↓
Draft
 ↓
Run Golden Dataset
 ↓
Compare Production vs Draft
 ↓
Pass
 ↓
Promote
 ↓
Observe
 ↓
必要时 Rollback
```

## 默认 Prompt 升级

StarMem 默认 Prompt 更新时：

如果用户未自定义：

```text
自动跟随默认版本
```

如果用户存在 Custom：

```text
New Default Available

[查看差异]
[合并更新]
[保持当前]
```

## 全局 User Instructions

除单个 Prompt 外，还应支持：

```text
Global AI Instructions
```

例如：

```text
- 技术记录优先保留原始命令
- 不把临时测试认定为最终配置
- 出现“最终、正式、以后”时提高 durable 权重
- hostname 常以 node- / host- / kvm 开头
```

这些规则可以组合进相关 Prompt。


# 2. 核心产品原则

必须严格遵守。

## 2.1 Raw First

Raw Entry 是最高事实来源。

AI 不允许：

- 修改原始内容
- 用摘要替代原文
- 把猜测写成用户事实
- 删除历史原始记录

---

## 2.2 Entry 与 Memory 分离

禁止将用户原文和 AI Memory 混在同一字段、同一概念中。

Entry：

```text
用户真正输入过的内容
```

Memory：

```text
从 Entry 中提炼出的长期事实 / 决策 / 配置 / 结论
```

---

## 2.3 AI 失败不能影响保存

必须保证：

```text
用户点击保存
↓
Raw Entry 立即持久化
↓
返回成功
↓
AI 后台异步处理
```

LLM、Embedding、Reranker、Redis 或 Worker 异常时：

- 不允许丢失 Raw Entry
- 不允许阻塞正常全文搜索
- UI 必须能看到 AI Job 失败状态
- 必须允许重试

---

## 2.4 Search First

禁止把目录树作为核心导航。

核心入口：

```text
记录
时间线
搜索
问记忆
Projects
Topics
Entities
```

---

## 2.5 所有 AI 回答必须可追溯

Ask / RAG 的回答必须返回来源。

每个来源至少包含：

- Entry ID
- 创建时间
- 原始内容片段
- 可跳转链接

AI 无可靠来源时，不允许生成确定性事实。

---

# 3. 禁止偏离方向

以下行为明确禁止：

- 第一阶段做多人系统
- 第一阶段做团队权限
- 第一阶段做复杂 RBAC
- 第一阶段做评论
- 第一阶段做 Kanban
- 第一阶段做 Notion 风格块编辑器
- 第一阶段做复杂知识图谱 UI
- 第一阶段引入 Elasticsearch / OpenSearch
- 第一阶段引入 Kubernetes
- 第一阶段过度拆微服务
- 所有搜索都调用 LLM
- 只做 Vector Search
- 用 Vector Search 取代全文搜索
- AI 自动修改 Raw Entry
- 把 Entry 和 Memory 混成一张概念表
- 重跑任务产生重复 Tag / Entity / Memory
- 因模型异常导致 Entry 保存失败
- 未完成基础可靠性就开始堆 AI Chat UI
- 未做测试就宣布完成
- 只给伪代码不实现
- 只生成设计文档不落地代码

---

# 4. 默认技术栈

除非现有项目已经使用等价且更合理的技术，否则按照以下方案。

## Frontend

```text
React
TypeScript
Vite
Tailwind CSS
shadcn/ui
TanStack Query
React Router
```

目标：

- 简洁
- 现代
- 扁平
- 信息密度合理
- 不做大量渐变
- 不做花哨视觉效果
- 优先可读性与效率

---

## Backend

```text
Python 3.12+
FastAPI
SQLAlchemy 2.x
Alembic
Pydantic v2
```

---

## Database

```text
PostgreSQL 16+
pgvector
pg_trgm
```

PostgreSQL 是唯一核心持久化数据库。

禁止为了 P0 加入：

```text
Elasticsearch
OpenSearch
MongoDB
Neo4j
```

---

## Queue

优先：

```text
Redis
Dramatiq
```

如果已有项目使用 Celery，可继续使用。

---

## Deployment

P0 必须：

```text
Docker Compose
```

至少包含：

```text
web
api
worker
postgres
redis
```

---

# 5. 实施方法

必须严格按阶段实施。

禁止跳 Phase。

每个 Phase 完成后必须：

1. 执行 Migration
2. 启动服务
3. 执行单元测试
4. 执行集成测试
5. 手工验证关键路径
6. 修复所有本 Phase 引入的问题
7. 更新 README / 实施记录
8. 再进入下一个 Phase

---

# 6. Phase 0：项目骨架

目标：

> 建立一个可靠、可启动、可测试的工程基础。

完成：

- 项目目录
- Frontend
- Backend
- PostgreSQL
- pgvector
- pg_trgm
- Redis
- Worker
- Docker Compose
- `.env.example`
- Alembic
- Health Check
- 基础认证
- iOS Safari 响应式基础
- PWA Manifest / apple-touch-icon / standalone
- Safe Area
- Mobile Bottom Navigation
- Source 基础模型
- `StarMem Native` Source
- ContentUnit 基础模型
- Prompt Registry 数据模型
- Prompt Version 数据模型
- Prompt Test Case 数据模型

- Structured Logging
- Request ID
- 单元测试框架
- 集成测试框架

要求：

```bash
docker compose up -d
```

后系统能够正常启动。

Health API：

```http
GET /health
```

必须验证：

- API
- DB
- Redis

---

# 7. Phase 1：Raw Memory

这是整个项目最重要的基础阶段。

这一阶段：

> 不依赖 LLM。

实现：

## Entry CRUD

```http
POST   /api/v1/entries
GET    /api/v1/entries
GET    /api/v1/entries/{id}
PATCH  /api/v1/entries/{id}
DELETE /api/v1/entries/{id}
```

---

## Entry 数据

至少支持：

```text
title
raw_content
content_format
content_type
created_at
updated_at
deleted_at
is_pinned
is_favorite
importance
```

---

## Mobile Capture / Timeline

Phase 1 同时必须保证：

- iPhone Safari 可完整使用
- Capture 在手机端可单手操作
- Bottom Navigation
- 长文本不横向撑破页面
- 草稿自动保存
- standalone PWA 可运行
- 登录状态保持

---

## Timeline

实现：

- 按日期分组
- 倒序
- 无限滚动 / cursor pagination
- 今天
- 昨天
- 本周
- 本月
- 日期范围
- Pin
- Favorite
- Edit
- Soft Delete

---

## Markdown

支持：

- Markdown
- Code Block
- JSON
- YAML
- Shell
- XML
- TOML
- INI

代码块必须完整显示和复制。

---

## Entry Version

每次用户修改 Raw Entry：

自动生成 EntryVersion。

必须支持：

- 查看版本
- Diff
- 恢复

---

## Full Text Search

实现：

```text
PostgreSQL tsvector
GIN index
pg_trgm
```

搜索必须适合技术文本。

重点支持：

- hostname
- IP
- UUID
- WWN
- error code
- path
- command
- domain
- model name

---

# 8. Phase 1 验收

必须至少验证：

## Case 1

保存：

```text
test memory
```

LLM 完全不存在时：

- 保存成功
- Timeline 可见
- Full Text Search 可找到

---

## Case 2

保存 20,000+ 字符日志：

- 原文完整
- 页面可打开
- 数据库内容一致

---

## Case 3

保存：

```text
WWN: 3600508b400105e210000900000490000
```

搜索完整 WWN。

要求：

> 该 Entry 第一名。

---

## Case 4

修改 Entry 3 次。

要求：

- 当前内容正确
- 存在完整三个版本
- 可查看历史

完成所有验收才进入 Phase 2。

---

# 9. Phase 2：Chunk + Embedding + Search

实现：

- 内容结构识别
- Chunk
- Embedding
- pgvector
- Semantic Search
- Hybrid Search

---

# 10. Chunk 原则

禁止简单固定长度暴力切分。

优先按结构：

```text
Markdown Heading
Paragraph
Code Block
Log Block
List
Table
```

推荐：

```text
300~800 tokens
overlap 50~120
```

但：

- Code Block 尽量完整
- traceback 尽量完整
- Shell 命令不能从中间切断
- YAML / JSON 配置尽量按逻辑块

---

# 11. Semantic Search

接口：

```http
GET /api/v1/search?mode=semantic&q=...
```

搜索结果必须返回：

- Entry
- Chunk
- Similarity Score
- Highlight / snippet

---

# 12. Hybrid Search

默认模式：

```text
hybrid
```

候选来源：

```text
Full Text
Vector
Entity
Memory
Temporal
```

当前 Phase 2 先实现：

```text
Full Text
+
Vector
```

后续再接 Entity / Memory。

权重必须可配置，禁止写死业务代码。

---

# 13. Exact Match Boost

实现 identifier 检测。

重点：

```text
IPv4 / IPv6
UUID
WWN
hostname
domain
file path
error code
model identifier
```

如果 Query 精确命中：

> Exact Match 必须显著高于 Semantic Similarity。

---

# 14. Phase 2 验收

保存：

```text
旧 iscsi session 没有清理导致 multipath 路径残留。
```

搜索：

```text
之前磁盘路径因为旧连接没释放的问题
```

要求：

> 原 Entry 进入 Top 5。

---

同时保存：

A：

```text
iscsi session 清理
```

B：

```text
iscsi 登录配置
```

C：

```text
multipath undef 是旧 iscsi session 残留造成
```

搜索：

```text
multipath undef iscsi
```

要求：

> C 排第一。

---

# 15. Phase 3：AI Enrichment + Prompt Engine

开始接 LLM。

在实现任何 AI 任务前，先完成：

- Prompt Registry
- Prompt Version
- Production / Draft 状态
- Output Schema Contract
- User Instructions
- Prompt Preview
- Prompt Test 基础能力
- AI Derivation Metadata

然后实现：



- Summary
- Classification
- Tagging
- Entity Extraction
- Temporal Extraction
- Project Detection
- Topic Detection
- Related Entry

---

# 16. AI Job

所有 AI 任务必须独立 Job。

例如：

```text
classify
summarize
tag
entity_extract
time_extract
project_classify
topic_classify
relation_build
```

每个 Job 必须：

- 状态可查询
- 有 attempt
- 有 error
- 有 model
- 有 provider
- 有 latency
- 可重试
- 幂等

---

# 17. Tag 规则

打标签前：

1. 搜索相似历史 Entry
2. 收集已有标签
3. 优先复用已有标签
4. 仅必要时创建新标签

禁止生成大量同义标签。

---

# 18. Entity

实体类型至少：

```text
host
ip
domain
project
software
service
model
hardware
company
person
location
error
command
api
file
repository
product
protocol
cluster
vm
container
storage
custom
```

例如：

```text
node-3903 上 multipath 出现 undef running
```

必须识别：

```text
Host=node-3903
```

---

# 19. AI Metadata 优先级

必须：

```text
User Created
>
User Confirmed AI
>
AI Generated
```

用户手工修改后：

> 后续重新处理不得覆盖。

---

# 20. Phase 3 验收

输入：

```text
node-3903 上旧 iscsi session 没有清理，
导致 multipath 出现 undef running。
```

要求至少得到：

```text
Type: 故障排查
Entity: node-3903 / Host
Tag: iSCSI
Tag: multipath
```

并且：

- 重跑 3 次不产生重复 Entity
- 重跑 3 次不产生重复 Tag

---

# 21. Phase 4：Memory Layer / Memory Engine

这是核心阶段。

必须按以下架构实现：

```text
Evidence
↓
Observation
↓
Memory Candidate
↓
Salience
↓
Retrieve Existing Memory
↓
Memory Reconcile
↓
Validator
↓
Transactional Apply
↓
Canonical Memory
↓
Knowledge
```

LLM 禁止直接写 Memory 表。

实现：

- Memory Extraction
- Salience Evaluation
- Retrieve-Before-Write
- Memory Source
- Memory Reconciliation
- ADD / SUPPORT / SUPERSEDE / CONFLICT / MERGE / IGNORE
- Reconcile scope serialization / 并发保护
- Supersede
- Conflict
- Active Memory
- Historical Memory
- Prompt version trace


- Memory Extraction
- Memory Source
- Memory Reconciliation
- Supersede
- Conflict
- Active Memory
- Historical Memory

---

# 22. Memory Extraction

只提取：

- 稳定事实
- 当前配置
- 已确认决策
- 长期约束
- 最终结论
- 解决方案
- 当前状态

不要把所有句子转换成 Memory。

---

# 23. Memory Structure

优先归一化：

```text
subject
predicate
value
```

例如：

```text
V100
power_limit
150W
```

---

# 24. Memory Reconciliation

新 Memory：

```text
subject + predicate
```

先查询现有 Memory。

情况：

## 无历史

创建 Active。

## 相同值

增加 supporting source。

## 不同值

判断：

- update
- historical
- conflict

---

# 25. Supersede

输入：

```text
V100 原来是 180W，后来最终固定 150W。
```

最终状态：

```text
180W → superseded
150W → active
```

禁止删除 180W。

---

# 26. Conflict

两个来源分别：

```text
Lumen 默认端口是 8080
```

和：

```text
Lumen 默认端口是 8081
```

没有明确时间更新关系。

必须：

- 不静默覆盖
- 标记 conflict
- UI 显示冲突
- 允许人工确认

---

# 27. Phase 4 验收

输入：

```text
V100 最终固定限制到 150W。
```

必须生成：

```text
subject=V100
predicate=power_limit
value=150W
status=active
```

---

再输入：

```text
V100 之前是 180W，后来改成 150W。
```

不得重新把 180W 变 Active。

---

# 28. Phase 5：Ask / RAG

实现：

```http
POST /api/v1/ask
```

流程：

```text
Query
↓
Query Understanding
↓
Keyword / Entity / Time
↓
Hybrid Retrieval
↓
Rerank
↓
Context Builder
↓
LLM
↓
Answer + Sources
```

---

# 29. Query Understanding

输出结构类似：

```json
{
  "intent": "troubleshooting_recall",
  "keywords": ["iscsi", "multipath"],
  "entities": [],
  "time_hint": "recent_past",
  "answer_mode": "procedure"
}
```

优先：

- Regex
- Rule
- Small Model

不要每个搜索 Query 都调用昂贵大模型。

---

# 30. Temporal Retrieval

至少支持：

```text
今天
昨天
上周
上个月
最近
前几天
前段时间
7月份
去年
第一次
最近一次
```

例如：

```text
我前段时间测试 V100 的结果
```

必须利用：

```text
Entity=V100
+
Semantic
+
Temporal Bias
```

---

# 31. Reranker

必须定义 Provider Interface。

例如：

```python
class RerankerProvider:
    def rerank(self, query, candidates):
        ...
```

允许：

- disabled
- local
- API

即使默认不启用，也必须支持。

---

# 32. Source Citation

每个 Ask Response：

```json
{
  "answer": "...",
  "confidence": 0.92,
  "sources": [
    {
      "entry_id": "...",
      "created_at": "...",
      "snippet": "...",
      "score": 0.94
    }
  ]
}
```

UI 必须：

- 展示来源
- 点击来源
- 跳到 Entry
- 高亮相关内容

---

# 33. Phase 5 验收

历史：

```text
V100 最终固定限制到 150W。
```

问题：

```text
我的 V100 最后设置多少瓦？
```

要求：

- 回答 150W
- 引用 150W Entry
- 不把 superseded 的历史值当当前值

---

# 34. Phase 6：P0 完成度

实现：

- AI Job 页面
- Reprocess
- Settings
- Provider Configuration
- Model Routing
- Backup
- Metrics
- Error Handling
- UI Polish
- README
- Deployment Documentation

---

# 35. AI Provider 抽象

必须统一接口。

例如：

```python
class ChatProvider:
    complete(...)

class EmbeddingProvider:
    embed(...)

class RerankerProvider:
    rerank(...)
```

至少兼容：

- OpenAI-compatible

架构必须允许未来增加：

- Ollama
- vLLM
- llama.cpp server
- custom HTTP

---

# 36. Model Routing

配置中必须允许分别指定：

```text
Classification Model
Summary Model
Tag Model
Entity Model
Memory Model
Chat Model
Embedding Model
Reranker
```

允许不同任务复用同一个模型。

---

# 37. Secret Detection

在远程 LLM 调用前提供 Hook。

检测：

- Password
- Private Key
- API Key
- Bearer Token
- Cookie
- AK/SK
- SSH Key
- DB Password

策略至少预留：

```text
allow
redact
local_only
block_remote
```

P0 可以基础实现，但接口必须完整。

---

# 38. 可观测性

必须记录：

- request_id
- entry_id
- job_id
- provider
- model
- latency
- token usage
- retry count
- search latency
- embedding latency
- error type

禁止把 Secret 写入日志。

---

# 39. 测试

目录至少：

```text
tests/
  api/
  models/
  search/
  memory/
  ai/
  workers/
  integration/
```

必须覆盖：

- Entry CRUD
- Soft Delete
- EntryVersion
- FTS
- pg_trgm
- Exact Identifier
- Semantic Search
- Hybrid Search
- Code Chunk
- Log Chunk
- Duplicate Tag
- Duplicate Entity
- Memory Extract
- Memory Supersede
- Memory Conflict
- AI Job Retry
- Provider Timeout
- Provider Failure
- Reprocess
- Source Citation
- iOS Responsive Layout
- PWA Manifest
- Safe Area
- Source Attribution
- ContentUnit Search
- Search Scope
- Prompt Version
- Prompt Rollback
- Prompt Schema Validation
- Prompt Golden Dataset
- User Instructions Override
- Salience
- Reconcile ADD
- Reconcile SUPPORT
- Reconcile SUPERSEDE
- Reconcile CONFLICT
- Reconcile MERGE
- Reconcile IGNORE
- Reconcile Concurrency

---

# 40. Mock Provider

测试环境必须提供：

```text
MockChatProvider
MockEmbeddingProvider
MockRerankerProvider
```

禁止让 CI 测试依赖真实外部 API。

---

# 41. 数据迁移

每次 schema 修改：

必须使用 Alembic Migration。

禁止：

- 手工改数据库不写 migration
- 启动时随意 create_all 替代 migration
- 破坏现有数据

---

# 42. 性能基线

按：

```text
100,000 Entries
500,000 Chunks
单用户
```

进行设计。

目标：

Raw Entry 保存：

```text
P95 < 300ms
```

全文搜索：

```text
P95 < 500ms
```

Hybrid Search：

```text
P95 < 1.5s
```

Ask 的本地 Retrieval：

```text
P95 < 2s
```

外部模型生成时间不计入本地 Retrieval SLA。

---

# 43. 前端设计约束

整体：

- shadcn/ui
- Tailwind
- 扁平
- 清晰
- 信息密度适中
- 内容区居中
- 不做大量渐变
- 不做大面积空白
- 技术型产品
- 明暗主题都需要可读

标签：

> 边框和填充色属于同一色系，文字保持高对比。

状态色需要有区分：

- Success
- Warning
- Error
- Processing
- AI
- User confirmed

---

# 44. 首页重点

首页不能做成 Dashboard 数据大屏。

第一视觉中心必须是：

```text
有什么需要记住的？
```

下面才是 Timeline。

---

# 45. Search UX

搜索结果应该突出：

- 为什么命中
- 时间
- Entity
- Tag
- Source
- Exact Match
- Semantic Match

如果是精确 identifier 命中：

显示：

```text
Exact match
```

---

# 46. Ask UX

必须明确分开：

```text
AI Answer
```

与：

```text
Sources
```

如果部分内容是推断：

明确标注：

```text
推断
```

禁止把推断伪装成历史记录事实。

---

# 47. AI Job UX

Entry 卡片可以展示：

```text
✓ 已索引
✓ 已生成 Embedding
✓ 已提取 Entity
✓ 已生成 Memory
```

失败：

```text
⚠ AI Processing Failed
[重新处理]
```

---

# 48. Docker Compose

必须最终做到：

```bash
cp .env.example .env
docker compose up -d
```

即可启动。

README 必须说明：

- 环境变量
- 初始化
- Migration
- 管理员创建
- Provider 配置
- Backup
- Restore
- Reprocess
- 全量重建 Embedding

---

# 49. Backup

至少提供：

```text
scripts/backup.sh
scripts/restore.sh
```

备份：

- PostgreSQL
- attachments（如果已启用）
- config

Embedding 可以重建，不视为不可恢复核心数据。

---

# 50. Error Handling

所有外部 Provider：

必须设置：

- timeout
- retry count
- backoff
- circuit protection / failure handling

禁止无限 retry。

---

# 51. 幂等

这些操作必须幂等：

```text
Embedding
Summary
Classification
Tagging
Entity Extraction
Memory Extraction
Related Entry
Reprocess
```

重复执行不能制造：

- duplicate tag
- duplicate entity
- duplicate memory
- duplicate relation

---

# 52. 数据唯一性

必须合理设计：

- unique index
- normalized field
- upsert
- transaction

不要只依赖“AI 应该不会重复”。

---

# 53. 开发纪律

每完成一个 Phase：

创建明确的实施记录：

```text
docs/implementation/phase-X.md
```

内容：

```text
完成内容
数据库变化
API
UI
测试
验收结果
已知限制
下一阶段
```

---

# 54. 不要频繁询问用户

如果实现过程中遇到普通工程细节缺失：

优先根据以下原则自行决策：

1. 简单
2. 稳定
3. 可维护
4. 可替换
5. 少依赖
6. 不扩 Scope
7. 与 PRD 一致

不要因为：

- 文件名
- 小 UI 细节
- 类名
- 内部目录
- 普通库选择

频繁停下来询问。

只有在：

> 无法继续且不同选择会导致明显产品方向变化

时才需要提出问题。

---

# 55. 遇到现有代码时

如果仓库已有代码：

先：

1. 阅读 README
2. 阅读目录结构
3. 阅读 package / dependency
4. 阅读 Docker 配置
5. 阅读数据库模型
6. 阅读现有测试

然后：

- 尽量复用已有架构
- 不无故重写
- 不破坏已有功能
- 先补测试再重构关键逻辑

---

# 56. 每阶段执行要求

不要只报告“建议”。

必须实际：

- 创建文件
- 修改代码
- 执行 Migration
- 执行测试
- 启动服务
- 检查日志
- 修复错误
- 再继续

---

# 57. 完成标准

项目只有满足以下要求才可以宣布 P0 完成：

- [ ] Raw Entry 不依赖 AI 即可保存
- [ ] Timeline 可正常使用
- [ ] Markdown / Code 正常
- [ ] Entry Version 正常
- [ ] Full Text Search 正常
- [ ] Exact Identifier Search 正常
- [ ] Chunk 正常
- [ ] Embedding 正常
- [ ] Semantic Search 正常
- [ ] Hybrid Search 正常
- [ ] AI Summary 正常
- [ ] AI Classification 正常
- [ ] AI Tag 正常
- [ ] Entity Extraction 正常
- [ ] Temporal Extraction 正常
- [ ] Related Entry 正常
- [ ] Memory Extraction 正常
- [ ] Memory Supersede 正常
- [ ] Memory Conflict 正常
- [ ] Ask 正常
- [ ] Source Citation 正常
- [ ] AI Job 可重试
- [ ] Reprocess 幂等
- [ ] Provider 可替换
- [ ] Docker Compose 一键启动
- [ ] Backup / Restore 可用
- [ ] README 完整
- [ ] 核心测试全部通过
- [ ] iOS Safari 完整可用
- [ ] iOS 主屏幕 standalone Web App 可用
- [ ] Mobile Bottom Navigation 正常
- [ ] Source / ContentUnit / Provenance 可用
- [ ] External Corpus 架构已预留
- [ ] Prompt Registry 可用
- [ ] Prompt Versioning 可用
- [ ] User Instructions 可编辑
- [ ] Prompt Schema Validation 可用
- [ ] Prompt Golden Dataset 可运行
- [ ] AI 派生结果记录 Prompt/Model/Schema 版本
- [ ] Memory Salience 正常
- [ ] Memory Reconcile 有有限 Operation
- [ ] Memory Reconcile 并发保护正常
- [ ] Evidence / Observation / Memory / Knowledge 分层完成


---

# 58. 最终交付报告

P0 完成后生成：

```text
docs/P0_COMPLETION_REPORT.md
```

必须包含：

## Architecture

实际最终架构。

## Features

已完成功能。

## Database

表结构和 Migration。

## Search

Full Text / Semantic / Hybrid 实际实现。

## Memory

Memory 生命周期实际实现。

## AI

Provider 和模型路由。

## Tests

测试数量、类型和结果。

## Performance

至少进行基础 benchmark。

## Known limitations

当前限制。

## P1 recommendation

下一阶段建议。

---

# 59. 最终产品行为

最终系统应满足：

```text
用户每天大量输入杂乱信息
       ↓
直接保存
       ↓
无需整理
       ↓
系统自动建立索引
       ↓
自动提取 Memory
       ↓
数月以后
       ↓
用户只记得模糊印象
       ↓
依然能够找到
       ↓
还能知道最新结论与历史变化
       ↓
所有答案都能回到原始来源
```

---

# 60. 现在开始

现在不要只输出设计建议。

请执行以下步骤：

1. 阅读 `starmem_v2_prd_architecture.md`
2. 检查当前仓库现状
3. 输出一个非常简短的实施状态说明
4. 从 Phase 0 开始实施
5. 每个 Phase 完成后运行其验收
6. 测试未通过不得进入下一阶段
7. 直到 P0 Definition of Done 全部满足
8. 最终生成 `docs/P0_COMPLETION_REPORT.md`

核心要求始终是：

> 可靠保存优先于 AI。

> 原始记录优先于派生信息。

> 搜索质量优先于花哨 UI。

> 引用来源优先于看似聪明但不可验证的回答。

> 先做可靠的个人记忆仓库，再做 AI。