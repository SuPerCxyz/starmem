# StarMem v2：PRD + 技术架构 + 数据模型 + 验收标准

版本：v0.2  
定位：单用户、自托管、零整理成本的StarMem  
目标读者：产品设计、后端、前端、AI/RAG、Codex/代码 Agent

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


# 1. 产品目标

构建一个面向个人长期使用的 AI 记忆仓库。

用户每天可能产生大量、杂乱、无结构的内容，包括：

- 技术问题
- 故障排查
- Shell 命令
- 配置片段
- 日志
- 项目需求
- 临时想法
- 性能测试
- 模型参数
- TODO
- 决策
- 网页
- 图片
- PDF
- 文档片段

用户不应在“记录”时承担整理成本。

核心目标：

> 用户负责输入，系统负责理解、索引、关联、记忆和找回。

最终系统必须支持两种找回方式：

1. 精确找回  
   - 时间
   - 关键词
   - 主机名
   - IP
   - UUID
   - WWN
   - 错误码
   - 标签
   - 实体

2. 模糊找回  
   - “我前段时间是不是遇到过一个 iSCSI 没清干净的问题？”
   - “之前 V100 最后到底设置多少瓦？”
   - “Lumen 默认端口后来是不是改过？”
   - “我以前处理过哪些类似的 multipath 残留问题？”

---

# 2. 非目标

第一阶段明确不做：

- 团队协作
- 多租户
- 复杂权限系统
- 评论系统
- Kanban
- 项目管理
- 日历管理
- 复杂块编辑器
- 类 Notion 页面搭建
- 强制目录树
- 保存前必须分类
- 保存前必须选择项目
- 保存前必须填写标题
- 以 Graph View 作为主界面
- AI 自动改写原始记录
- AI 自动删除历史事实
- 强依赖任意单一模型厂商
- 为了“漂亮”而增加无业务价值的复杂 UI

---

# 3. 核心原则

## 3.1 Raw First

用户原始内容是最高事实来源。

AI 可以：

- 摘要
- 标签
- 分类
- 实体提取
- 关联
- Memory 提取
- Knowledge Summary

AI 不可以：

- 静默修改原文
- 用 AI 摘要覆盖原文
- 删除历史原文
- 把推测写成用户事实

---

## 3.2 Zero Organization

记录时不能强迫用户：

- 想标题
- 想目录
- 想标签
- 想分类
- 想项目

入口必须接近：

```text
有什么需要记住的？

[                         ]
[                         ]
[                         ]

                     保存
```

---

## 3.3 Search First

系统的主要信息组织方式不是目录，而是：

- Timeline
- Search
- Ask
- Project
- Topic
- Entity
- Dynamic View

---

## 3.4 Memory ≠ Entry

必须明确区分：

### Entry

用户真正输入过的原始记录。

### Memory

AI 从 Entry 中抽取出的、适合长期复用的事实或结论。

例如：

Entry：

```text
V100 测试下来限制到 150W 性能损失比较小，
所以服务器以后就一直按照 150W 跑。
```

Memory：

```text
subject: V100
predicate: power_limit
value: 150W
status: active
```

---

## 3.5 Source Traceable

所有 AI 回答必须能追溯到原始记录。

不能只回答：

```text
V100 是 150W。
```

必须能展示：

```text
V100 当前长期功耗限制为 150W。

来源：
2026-09-15 11:23
[V100 测试记录]
```

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


# 4. 用户主流程

## 4.1 记录

```text
用户输入
   ↓
立即保存 Raw Entry
   ↓
返回成功
   ↓
后台异步 AI Processing
```

“保存成功”不依赖 AI。

即使：

- LLM 挂了
- Embedding 服务挂了
- Reranker 挂了
- Redis 挂了

只要数据库可写，原始记录就必须保存。

---

## 4.2 搜索

```text
用户 Query
   ↓
Query Parser
   ↓
Exact / Full Text / Semantic / Entity / Time
   ↓
Candidate Merge
   ↓
Rerank
   ↓
Results
```

---

## 4.3 Ask

```text
用户自然语言问题
   ↓
Query Understanding
   ↓
Intent / Entity / Time / Keywords
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

# 5. P0 页面结构

P0 一级导航：

```text
+ 记录

时间线

搜索

问记忆

────────────

Projects
Topics
Entities

────────────

AI 任务
设置
```

---

# 6. 首页 / Capture

## 6.1 输入框

必须支持：

- 多行输入
- Markdown
- Code Block
- 超长文本
- Shell 命令
- 日志
- JSON
- YAML
- XML
- TOML
- INI
- SQL
- Ctrl+Enter 保存
- 自动保存草稿

---

## 6.2 保存行为

点击保存后：

1. Raw Entry 立即写数据库
2. 立即在 Timeline 展示
3. AI 状态显示 Processing
4. Worker 异步处理
5. 页面通过 polling / SSE / WebSocket 更新状态

---

# 7. Timeline

必须：

- 按日期分组
- 无限滚动
- 今天
- 昨天
- 本周
- 本月
- 日期跳转
- 时间区间过滤
- Pin
- Favorite
- 编辑
- 删除
- 查看原文
- 查看 AI Metadata
- 查看相关 Entry
- 查看关联 Memory

卡片建议展示：

```text
13:42

node-3903 multipath 出现 undef running...

故障排查  #Storage  #iSCSI  #multipath

node-3903 · Cinder

✓ 已索引
```

---

# 8. Search 页面

搜索栏：

```text
搜索任何记忆……
```

搜索模式：

```text
● 智能
○ 全文
○ 语义
```

过滤项：

- 时间
- Entry Type
- Project
- Topic
- Entity
- Tag
- Favorite
- Pinned
- AI Processing 状态

排序：

- 综合相关度
- 最新
- 最早
- 最近更新

---

# 9. Ask 页面

结构：

```text
┌─────────────────────────────────────┐
│ 我之前那个 iscsi 没清干净的问题？    │
└─────────────────────────────────────┘

回答……

来源 3

[2026-09-11 14:23]
[2026-08-12 17:51]
[2026-08-15 09:30]
```

必须支持：

- 继续追问
- 展开来源
- 点击来源跳 Entry
- 显示 AI 引用了哪些来源
- 明确标识“事实”和“推断”
- 无可靠来源时禁止伪造确定答案

---

# 10. P0 技术栈

推荐默认实现：

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- TanStack Query
- React Router

不建议 P0 使用重量级 SSR。

原因：

- 单用户
- 自托管
- Dashboard / SPA 场景
- SEO 没有价值

---

## Backend

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic v2

原因：

- AI / Embedding / RAG Python 生态成熟
- API 简单
- 异步 Worker 容易集成

---

## Database

P0：

- PostgreSQL 16+
- pgvector

用途：

- Entry
- Metadata
- Memory
- Entity
- Relation
- Full Text Search
- Vector Search

原则：

> P0 不上 Elasticsearch / OpenSearch。

PostgreSQL 已足够支撑单用户个人知识库。

---

## Queue / Worker

推荐：

- Redis
- Dramatiq

也可以：

- Celery

优先 Dramatiq，原因：

- 更轻
- Worker 模型简单
- 更适合当前项目规模

---

## Object Storage

P0 文本阶段可以先不用。

P1 附件支持：

- 本地 filesystem
或
- S3 compatible
- MinIO

需要统一 Storage Interface。

---

# 11. Docker Compose 架构

P0：

```text
starmem-web
    ↓
starmem-api
    ↓
PostgreSQL + pgvector

starmem-api
    ↓
Redis
    ↓
starmem-worker

starmem-worker
    ↓
LLM Provider
Embedding Provider
Reranker Provider
```

建议服务：

```yaml
services:
  web:
  api:
  worker:
  postgres:
  redis:
```

P1 可加入：

```yaml
  minio:
```

---

# 12. 数据模型总览

核心对象：

```text
Entry
 ├─ EntryVersion
 ├─ EntryChunk
 ├─ Tag
 ├─ Entity
 ├─ Project
 ├─ Topic
 ├─ Memory
 ├─ Relation
 └─ AIJob
```

---


# 新增核心表：sources

```sql
id                  uuid primary key
name                text not null
source_type         varchar(64) not null
description         text null
config_json         jsonb
is_enabled          boolean default true
created_at          timestamptz
updated_at          timestamptz
```

内置：

```text
StarMem Native
```

---

# 新增核心表：external_items

```sql
id                  uuid primary key
source_id           uuid not null

external_id         text not null
external_parent_id  text null

item_type           varchar(64)
title               text null
raw_content         text null

external_created_at timestamptz null
external_updated_at timestamptz null

content_hash        text null
metadata_json       jsonb

last_synced_at      timestamptz null

created_at          timestamptz
updated_at          timestamptz
```

---

# 新增核心表：content_units

```sql
id                  uuid primary key

owner_type          varchar(32) not null
owner_id            uuid not null

source_id           uuid not null

unit_type           varchar(64)
sequence            integer

content             text not null
event_time          timestamptz null

metadata_json       jsonb

fts_vector          tsvector
embedding           vector

created_at          timestamptz
updated_at          timestamptz
```

Search Layer 应优先以 ContentUnit 为最小检索单位。

---

# 新增核心表：prompt_definitions

```sql
id                  uuid primary key
name                text not null
description         text null
created_at          timestamptz
updated_at          timestamptz
```

---

# 新增核心表：prompt_versions

```sql
id                  uuid primary key
prompt_definition_id uuid not null

version_number      integer not null
status              varchar(32) not null

prompt_text         text not null
user_instructions   text null

provider            text null
model               text null

temperature         float null
top_p               float null
max_tokens          integer null

input_schema_version  text null
output_schema_version text null

prompt_hash         text not null

created_at          timestamptz
created_by          varchar(32)

unique(prompt_definition_id, version_number)
```

---

# 新增核心表：prompt_test_cases

```sql
id                  uuid primary key
prompt_definition_id uuid not null

name                text not null
input_json          jsonb not null
expected_json       jsonb null
assertions_json     jsonb null

is_builtin          boolean default false

created_at          timestamptz
updated_at          timestamptz
```

---

# 新增核心表：ai_derivation_meta

用于记录 AI 派生数据的生成来源。

可作为独立表，也可作为公共字段 / JSONB 混入各派生表。

至少记录：

```text
provider
model
prompt_name
prompt_version
schema_version
prompt_hash
generated_at
```



# 13. entries 表

建议字段：

```sql
id                  uuid primary key

title               text null
raw_content         text not null
content_format      varchar(32)
content_type        varchar(64)

source_type         varchar(32)
source_uri          text null

created_at          timestamptz
updated_at          timestamptz
deleted_at          timestamptz null

event_time_start    timestamptz null
event_time_end      timestamptz null

is_pinned           boolean default false
is_favorite         boolean default false

importance          smallint default 0

ai_status           varchar(32)
ai_version          integer default 0

fts_vector          tsvector
```

---

# 14. entry_versions 表

用于保存 Raw Entry 修改历史。

字段：

```sql
id
entry_id
version_number
raw_content
title
created_at
change_source
```

change_source：

- user
- import
- system

AI 禁止生成 Raw Entry version。

---

# 15. entry_chunks 表

Chunk 只服务于检索。

字段：

```sql
id
entry_id
chunk_index
chunk_type
content
token_count
embedding
start_offset
end_offset
metadata jsonb
```

chunk_type：

- prose
- code
- log
- config
- table
- heading
- mixed

---

# 16. tags 表

```sql
id
name
normalized_name
created_at
source
```

source：

- user
- ai
- imported

---

# 17. entry_tags 表

```sql
entry_id
tag_id
source
confidence
user_confirmed
created_at
```

---

# 18. entities 表

```sql
id
entity_type
canonical_name
normalized_name
description
metadata jsonb
created_at
updated_at
```

entity_type：

- host
- ip
- domain
- project
- software
- service
- model
- hardware
- company
- person
- location
- error
- command
- api
- file
- repository
- product
- protocol
- cluster
- vm
- container
- storage
- custom

---

# 19. entry_entities 表

```sql
entry_id
entity_id
mention_text
confidence
source
created_at
```

---

# 20. projects 表

```sql
id
name
description
source
status
created_at
updated_at
```

source：

- user
- ai
- imported

status：

- active
- archived

---

# 21. topics 表

```sql
id
name
parent_id null
description
source
created_at
updated_at
```

Topic 可以形成轻量层级，但不作为用户必须维护的目录。

---

# 22. memories 表

Memory 是核心表。

```sql
id                  uuid primary key

subject_type        varchar(64)
subject_key         text
predicate           text
value_json          jsonb
memory_text         text

status              varchar(32)

confidence          float

valid_from          timestamptz null
valid_to            timestamptz null

created_at          timestamptz
updated_at          timestamptz

superseded_by       uuid null

source_entry_id     uuid
source_chunk_id     uuid null

embedding           vector
metadata            jsonb
```

status：

```text
active
superseded
conflicted
expired
deleted
```

---

# 23. memory_sources 表

一个 Memory 可以来自多个 Entry。

```sql
memory_id
entry_id
chunk_id null
support_type
confidence
```

support_type：

- primary
- supporting
- contradicting

---

# 24. relations 表

统一关系表：

```sql
id
source_type
source_id
relation_type
target_type
target_id
confidence
source
created_at
```

relation_type 示例：

```text
mentions
related_to
belongs_to
supersedes
contradicts
supports
derived_from
same_incident
same_project
same_entity
same_topic
```

---

# 25. ai_jobs 表

```sql
id
entry_id
job_type
status
provider
model
attempt
error
started_at
finished_at
created_at
```

job_type：

- classify
- summarize
- tag
- entity_extract
- time_extract
- memory_extract
- embedding
- relation_build
- topic_classify
- project_classify

status：

- pending
- running
- success
- failed
- retrying

---

# 26. AI Processing Pipeline

Entry 保存后：

```text
1. normalize
2. content detection
3. chunk
4. FTS index
5. embedding
6. classify
7. summarize
8. tag
9. entity extraction
10. temporal extraction
11. project / topic detection
12. memory extraction
13. memory reconciliation
14. related entry detection
```

其中：

- 1~4 不依赖 LLM
- 5 依赖 Embedding
- 6~13 依赖 AI
- 14 可结合向量和实体完成

---

# 27. Pipeline 幂等要求

所有 AI Job 必须幂等。

重复执行：

```text
entry_123 summarize
```

不能不断生成重复 Summary。

重复执行：

```text
entry_123 entity_extract
```

不能无限新增相同 Entity。

必须通过：

- normalized key
- unique constraint
- version
- upsert

实现。

---

# 28. Chunk 策略

禁止固定每 500 token 无脑切。

优先结构切分：

```text
Markdown Heading
Paragraph
Code Block
Log Block
List
Table
```

目标 Chunk：

- 300~800 tokens
- overlap 50~120 tokens

但 Code Block：

> 原则上保持完整。

日志：

- 按事件块
- 按 traceback
- 按时间段
- 按错误边界

---

# 29. Full Text Search

PostgreSQL：

- `tsvector`
- GIN index

同时必须保留：

- ILIKE / trigram

建议安装：

```text
pg_trgm
```

用于：

- Hostname
- UUID
- WWN
- 模糊字符串
- 拼写片段

---

# 30. Vector Search

Embedding：

- Entry Chunk embedding
- Memory embedding
- 可选 Entity description embedding

不能只给整个 Entry 一个 embedding。

原因：

- Entry 可能非常长
- 混合多个主题
- 技术日志尤其明显

---

# 31. Hybrid Search 算法

P0 推荐：

```text
Keyword Candidates
Semantic Candidates
Entity Candidates
Memory Candidates
Temporal Filter
      ↓
Merge
      ↓
Score Normalize
      ↓
Weighted Score
      ↓
Rerank
```

初始权重可配置：

```text
keyword       0.30
semantic      0.30
entity        0.15
memory        0.10
temporal      0.05
recency       0.05
importance    0.05
```

不能写死。

---

# 32. Exact Identifier Boost

对于以下内容：

- IP
- UUID
- WWN
- Hostname
- Error Code
- Model Name
- Domain
- File Path

如果 Query 精确命中：

> 必须获得极高 boost。

例如：

```text
3600508b400105e210000900000490000
```

精确结果应该排在语义相似内容之前。

---

# 33. Query Understanding

Ask 和智能搜索先做轻量解析。

输出：

```json
{
  "intent": "troubleshooting_recall",
  "keywords": ["iscsi", "multipath"],
  "entities": [],
  "time_hint": "recent_past",
  "answer_mode": "procedure"
}
```

Query Parser 可以：

- 规则
- regex
- 小模型

组合完成。

不要任何 Query 都强制调用昂贵大模型。

---

# 34. Temporal Retrieval

必须识别：

```text
今天
昨天
上周
最近
前几天
前段时间
7 月份
今年夏天
第一次
最近一次
```

Temporal Score 不等于数据库简单时间过滤。

例如：

```text
我前段时间测试 V100 的结果
```

应：

- Entity = V100
- Semantic = performance test
- Recency / Temporal Bias = recent

---

# 35. Reranker

P0 接口必须抽象：

```python
class Reranker:
    rerank(query, candidates) -> ranked_candidates
```

Provider 可实现：

- local model
- API model
- disabled

即使 P0 默认关闭，也必须预留。

---

# 36. Memory Extraction

AI 只抽取：

- 稳定事实
- 决策
- 配置
- 当前状态
- 长期偏好
- 已确认结论
- 解决方案
- 项目约束

不要把所有句子都转 Memory。

不应该生成：

```text
今天好累。
```

除非这是用户明确希望长期保存的信息。

---

# 37. Memory Key

Memory 尽量归一化为：

```text
subject + predicate
```

例如：

```text
V100 + power_limit
Lumen + default_port
node-3903 + storage_issue
Qwen-4B + deployment_backend
```

---

# 38. Memory Reconciliation

新 Memory 进入时：

```text
New Memory
   ↓
Search same subject + predicate
   ↓
No match
   → insert active

Same value
   → add supporting source

Different value
   ↓
LLM / Rules compare
   ↓
Update?
Conflict?
Historical?
```

---

# 39. Supersede

例如：

历史：

```text
Lumen.default_port = 8080
```

新记录：

```text
默认端口现在改成 8081
```

生成：

```text
old.status = superseded
old.superseded_by = new.id

new.status = active
```

历史必须保留。

---

# 40. Conflict

如果 AI 无法判断：

```text
A：默认端口 8080
B：默认端口 8081
```

且没有：

```text
改成
现在
后来
最终
```

之类的更新信号，则：

```text
A.status = conflicted
B.status = conflicted
```

UI 显示：

```text
Memory 冲突，需要确认
```

---

# 41. Related Entry

Related Entry Score：

```text
semantic similarity
shared entity
shared project
shared topic
shared tags
time proximity
```

默认每条 Entry：

- 展示 Top 5
- 最多计算 Top 20 缓存

---

# 42. Tag Generation

AI 打标签前：

```text
1. Search similar entries
2. Collect existing tags
3. Ask model to reuse existing tags first
4. Only create new tag if necessary
```

必须避免：

```text
Docker
docker
docker-container
Docker容器
容器Docker
```

无限膨胀。

---

# 43. Entity Normalization

例如：

```text
PostgreSQL
postgres
Postgres
PG
```

不能自动简单认为完全相同。

需要：

```text
canonical_name
alias
normalized_name
```

P1 可以加入 entity alias 表。

---

# 44. AI Provider Abstraction

统一接口：

```python
class ChatProvider:
    complete(...)

class EmbeddingProvider:
    embed(...)

class RerankerProvider:
    rerank(...)
```

支持：

- OpenAI-compatible
- Ollama
- vLLM
- llama.cpp server
- custom HTTP

---

# 45. Model Routing

设置：

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

允许多个任务共用一个模型。

---

# 46. Secret Detection

在内容发送给远端 LLM 之前运行。

检测：

- Private Key
- API Key
- Bearer Token
- Cookie
- Password
- AK/SK
- SSH Key
- DB Password

策略：

```text
allow
redact
local_only
block_remote
```

Entry 原文仍保存在本地。

---

# 47. API 设计

## Entry

```http
POST   /api/v1/entries
GET    /api/v1/entries
GET    /api/v1/entries/{id}
PATCH  /api/v1/entries/{id}
DELETE /api/v1/entries/{id}
```

---

## Search

```http
GET /api/v1/search
```

参数：

```text
q
mode=hybrid|fulltext|semantic
from
to
type
tag
entity
project
topic
limit
cursor
```

---

## Ask

```http
POST /api/v1/ask
```

Request：

```json
{
  "query": "之前那个 iscsi 没清干净的问题怎么处理？"
}
```

Response：

```json
{
  "answer": "...",
  "sources": [],
  "confidence": 0.91
}
```

---

## Memories

```http
GET   /api/v1/memories
GET   /api/v1/memories/{id}
PATCH /api/v1/memories/{id}
```

---

## AI Jobs

```http
GET  /api/v1/ai/jobs
POST /api/v1/entries/{id}/reprocess
```

---

# 48. MCP Server

P1，但 P0 架构必须预留。

Tools：

```text
starmem_add
starmem_search
starmem_get
starmem_ask
starmem_find_related
starmem_get_entity
starmem_get_project
```

---

# 49. CLI

P1：

```bash
starmem add "..."
```

```bash
cat log.txt | starmem add --type log
```

```bash
starmem search "multipath undef"
```

```bash
starmem ask "之前 iscsi 残留怎么处理"
```

---

# 50. P1 文件支持

统一 Attachment：

```text
Entry
 └─ Attachment
```

支持：

- Image
- Screenshot
- PDF
- TXT
- Markdown
- JSON
- YAML
- Log

Attachment 保存：

```sql
attachments
-----------
id
entry_id
filename
mime_type
size
storage_key
sha256
created_at
```

---

# 51. URL Archive

P1：

```text
URL
 ↓
Fetch
 ↓
Extract readable content
 ↓
Store raw snapshot
 ↓
Create Entry
 ↓
AI pipeline
```

保存：

- URL
- Title
- HTML Snapshot
- Extracted Text
- Fetched Time
- HTTP Metadata

---

# 52. PWA / Mobile

P1：

- PWA
- responsive
- Share Target
- mobile quick capture

目标：

手机把：

- 文本
- URL
- 图片

分享进系统，3 步以内完成。

---

# 53. Backup

P0 必须提供文档和脚本。

备份至少包括：

- PostgreSQL
- Attachment storage
- Application config

Embedding：

> 不视为核心备份内容，可重新生成。

---

# 54. 可观测性

必须：

- structured log
- request id
- job id
- entry id
- AI provider latency
- AI provider error
- token usage
- embedding latency
- search latency

UI 设置页可显示：

```text
今日处理 Entry
AI 成功率
失败 Job
平均搜索耗时
```

---

# 55. 安全

P0：

- 单用户认证
- Session cookie
- CSRF 防护
- 密码 hash
- Rate Limit
- CORS 白名单
- API Token

不需要：

- RBAC
- Organization
- Team

---

# 56. 性能目标

假设：

- 100,000 Entries
- 500,000 Chunks
- 单用户

目标：

### 保存

Raw Entry：

```text
P95 < 300 ms
```

不包含 AI。

### 全文搜索

```text
P95 < 500 ms
```

### Hybrid Search

不包含外部 reranker：

```text
P95 < 1.5 s
```

### Ask

检索部分：

```text
P95 < 2 s
```

LLM 输出时间不作为本地检索 SLA。

---

# 57. P0 验收标准

以下全部满足，P0 才算完成。

---

## A. Capture

### A1

输入：

```text
test memory
```

点击保存。

要求：

- 立即出现在 Timeline
- 数据库存在
- 即使 LLM 服务关闭也能保存

PASS / FAIL

---

## A2

输入超过 20,000 字符日志。

要求：

- 保存成功
- 原文不丢失
- UI 可正常展开
- 后台可 Chunk

---

## A3

输入 Markdown + Shell Code Block。

要求：

- Markdown 正常显示
- Code Block 不损坏
- 复制代码内容一致

---

# 58. Timeline 验收

## B1

连续创建 30 条 Entry。

要求：

- 按时间倒序
- 日期分组正确
- 无限滚动正常

---

## B2

修改历史 Entry。

要求：

- Entry 内容更新
- EntryVersion 新增版本
- 历史版本仍可查看

---

# 59. Full Text Search 验收

创建：

```text
WWN: 3600508b400105e210000900000490000
```

搜索完整 WWN。

要求：

- 第一名必须是该 Entry
- 命中字符串高亮

---

# 60. Semantic Search 验收

Entry：

```text
旧 iscsi session 没有清理导致 multipath 路径残留。
```

Query：

```text
之前磁盘路径因为旧连接没释放的问题
```

要求：

- 该 Entry 必须进入 Top 5

---

# 61. Hybrid Search 验收

同时存在：

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

Query：

```text
multipath undef iscsi
```

要求：

- C 排名第一

---

# 62. Entity 验收

Entry：

```text
node-3903 上 multipath 出现 undef running。
```

要求自动生成：

```text
Host: node-3903
```

搜索：

```text
node-3903
```

要求：

- 能过滤该 Host 的全部 Entry

---

# 63. Memory 验收

输入：

```text
V100 最终固定限制到 150W。
```

要求生成：

```text
subject=V100
predicate=power_limit
value=150W
status=active
```

---

# 64. Memory Supersede 验收

已有：

```text
V100 power_limit = 180W
```

新增：

```text
V100 最终改成 150W。
```

要求：

```text
180W → superseded
150W → active
```

且 180W 不删除。

---

# 65. Memory Conflict 验收

分别输入：

```text
Lumen 默认端口是 8080
```

```text
Lumen 默认端口是 8081
```

第二条没有“改成”“现在”“后来”等更新语义。

要求：

- 系统不得静默覆盖
- Memory 标记 conflict 或进入待确认状态

---

# 66. Ask 验收

用户问：

```text
我的 V100 最后设置多少瓦？
```

要求：

- 回答 150W
- 引用包含 150W 的原始 Entry
- 不引用被 superseded 的 180W 作为当前答案

---

# 67. Source 验收

Ask 输出的每个来源必须：

- 有 Entry ID
- 有时间
- 可点击
- 点击后可以看到 Raw Entry

---

# 68. AI Failure 验收

关闭 LLM。

新增 Entry。

要求：

- Entry 成功保存
- AI Job 标记 failed / retry
- UI 显示 AI Processing Failed
- Full Text Search 仍然可搜到

---

# 69. Reprocess 验收

恢复 LLM。

点击：

```text
重新处理
```

要求：

- Job 重试
- AI Metadata 成功生成
- 不重复生成相同 Tag / Entity

---

# 70. 删除验收

删除 Entry：

要求：

- 默认 soft delete
- Timeline 不显示
- 默认 Search 不显示
- 数据仍可恢复

---

# 71. P0 开发阶段

建议按阶段实施。

## Phase 0：项目骨架

- Docker Compose
- Frontend
- API
- PostgreSQL
- Redis
- Worker
- Migration
- Auth

---

## Phase 1：Raw Memory

- Entry CRUD
- Timeline
- Markdown
- Version History
- Full Text Search

这一阶段完全不接 LLM。

必须先做到：

> 即使没有 AI，也是一个可靠的个人记录仓库。

---

## Phase 2：Embedding

- Chunk
- Embedding
- pgvector
- Semantic Search
- Hybrid Search

---

## Phase 3：AI Enrichment

- Summary
- Classification
- Tags
- Entities
- Temporal Extraction
- Related Entries

---

## Phase 4：Memory

- Memory Extraction
- Memory Source
- Memory Reconciliation
- Supersede
- Conflict

---

## Phase 5：Ask

- Query Understanding
- Hybrid Retrieval
- Context Builder
- RAG
- Source Citation
- Follow-up

---

## Phase 6：P0 Polish

- AI Job UI
- Reprocess
- Settings
- Provider config
- Backup
- Metrics
- Error handling

---


# 新增 P0 验收：iOS / Mobile

## M1

使用 iPhone Safari 登录。

要求：

- 登录成功
- Timeline 可用
- Capture 可用
- Search 可用
- Ask 可用
- 页面无横向溢出

## M2

添加到 iOS 主屏幕。

要求：

- 有 StarMem Icon
- standalone 运行
- safe-area 正常
- 登录状态保持
- 打开后可直接进入 StarMem

## M3

编辑长 Markdown / Code Block。

要求：

- 代码可横向滚动或适配
- 页面主体不被撑破
- Bottom Navigation 不遮挡内容

---

# 新增 P0 验收：Source / ContentUnit

## S1

Native Entry 保存后：

要求：

- 关联 `StarMem Native` Source
- 生成 ContentUnit
- Search 可以基于 ContentUnit 返回命中
- Source Attribution 正确

## S2

模拟 External Source 数据（无需真正 Connector）。

要求：

- 可以通过测试 fixture 创建 External Item
- 生成 ContentUnit
- Search Scope 能区分 Native / External
- Ask Source Citation 能显示来源差异

---

# 新增 P0 验收：Prompt Engine

## P1

修改 `Memory Extract` 的 User Instructions。

要求：

- 创建新 Prompt Version
- 历史版本不被覆盖
- 可以查看当前 Production Version

## P2

模型返回不符合 Output Schema。

要求：

- Validation Failed
- 不写入 Memory
- AI Job 显示失败原因

## P3

执行 Prompt Test。

要求：

- 可运行 Built-in Golden Dataset
- 可查看 Passed / Failed
- Draft 不会自动变 Production

## P4

Promote 新版本后重新处理 Entry。

要求：

- 新 AI 派生结果记录新的 prompt_version
- 可追踪旧结果使用的历史 prompt_version

---

# 新增 P0 验收：Memory Reconcile / Salience

## R1

已有：

```text
V100 power_limit = 150W [ACTIVE]
```

新增：

```text
刚才临时测试 175W。
```

要求：

- 不得把 150W 自动 supersede
- 175W 应为 episodic / ignore durable memory

## R2

已有：

```text
V100 power_limit = 180W [ACTIVE]
```

新增：

```text
V100 最终改成 150W。
```

要求：

- 180W → superseded
- 150W → active
- 历史保留

## R3

两个 Worker 同时处理同一个：

```text
V100:power_limit
```

要求：

- 不生成重复 Active Memory
- transaction / unique constraint / scope serialization 生效


# 72. Definition of Done

P0 完成必须满足：

1. 无 AI 仍可正常记录、编辑、全文搜索
2. Semantic Search 可独立工作
3. Hybrid Search 默认开启
4. AI Metadata 与 Raw Entry 分离
5. Memory 与 Entry 分离
6. Memory 有完整生命周期
7. Ask 必须引用来源
8. AI 失败不能导致数据丢失
9. 所有后台 Job 可重试
10. 所有 AI 任务幂等
11. 模型 Provider 可替换
12. PostgreSQL 是唯一核心数据源
13. Embedding 可全部重建
14. 原始数据可备份和恢复
15. 关键技术内容不被错误 Chunk
16. 精确 Identifier 搜索优先于语义相似结果
17. 人工修改永远优先于 AI 判断
18. 不为了功能数量牺牲记录速度

19. iOS Safari 和 Home Screen Web App 可作为正式入口
20. 移动端布局不是桌面缩小版
21. Source / ContentUnit / Provenance 从 P0 可用
22. External Corpus 不实现具体 Connector，但架构无需未来重构
23. Prompt Registry 可用
24. 用户可编辑 User Instructions
25. Prompt Versioning / History / Rollback 可用
26. Output Schema Validation 生效
27. AI 派生结果记录 model + prompt version + schema version
28. Memory Salience 生效
29. Memory Reconcile 只允许有限 Operation
30. Reconcile 有并发保护
31. Evidence / Observation / Memory / Knowledge 分层明确


---

# 73. Codex 实施约束

交给 Codex 开发时必须遵守：

## 禁止

- 未完成 Phase 1 就先做 AI Chat
- 为了方便直接把 Entry 和 Memory 混在同一张表
- 让 AI 直接改 Raw Entry
- 只使用 Vector Search
- 所有搜索都依赖 LLM
- 把全文搜索外包给大模型
- 为每个 Entry 创建大量无意义标签
- 重跑 AI 后产生重复 Entity / Tag / Memory
- 第一阶段引入 Elasticsearch
- 第一阶段引入 Kubernetes
- 第一阶段引入微服务拆分
- 第一阶段做复杂 Graph UI
- 第一阶段做多人权限
- 第一阶段做 Notion 风格编辑器

---

# 74. Codex 实施原则

必须：

- 小步提交
- 每个 Phase 都能运行
- Migration 可回滚
- API 有单元测试
- Search 有固定测试数据集
- Memory Reconciliation 有单元测试
- AI Provider 使用 Mock 测试
- Docker Compose 一键启动
- `.env.example` 完整
- README 包含初始化方法
- 每个 AI Job 可独立重试
- 所有外部 Provider 都必须设置 Timeout
- 对外部 AI 调用设置重试上限
- 不允许无限重试

---

# 75. 测试建议

至少包含：

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

重点测试：

- exact identifier search
- Chinese semantic search
- code chunk
- log chunk
- memory supersede
- memory conflict
- duplicate tag
- duplicate entity
- provider timeout
- provider unavailable
- worker retry
- entry soft delete
- entry version
- source citation

---

# 76. 初始目录结构建议

```text
starmem/
├── apps/
│   ├── web/
│   └── api/
│
├── worker/
│
├── packages/
│   ├── ai/
│   ├── search/
│   ├── memory/
│   └── common/
│
├── migrations/
│
├── tests/
│
├── docker/
│
├── scripts/
│
├── docker-compose.yml
├── .env.example
└── README.md
```

如果使用 Python Monorepo，也可以：

```text
backend/
  app/
    api/
    models/
    schemas/
    services/
    search/
    memory/
    ai/
    workers/
```

不要为了“架构漂亮”过度拆包。

---

# 77. P1 路线

P0 稳定后再进入：

- URL
- Web Archive
- Image
- OCR
- PDF
- Attachment
- Project Auto Cluster
- Topic Auto Cluster
- Saved Search
- Smart View
- Daily Review
- Weekly Review
- CLI
- MCP
- Browser Extension
- PWA
- Import / Export
- Secret Detection
- Local-only AI Rule

---

# 78. P2 路线

之后再考虑：

- Knowledge Graph UI
- Topic Evolution
- Advanced Memory Consolidation
- Multi-source sync
- GitHub ingestion
- Email ingestion
- Chat history ingestion
- Agent proactive memory retrieval
- Knowledge gap detection
- Long-term trend analysis
- Personal knowledge synthesis

---

# 79. 最终产品标准

最终系统应做到：

```text
大量杂乱信息
       ↓
直接输入
       ↓
不需要整理
       ↓
自动理解
       ↓
自动形成索引与 Memory
       ↓
数月以后
       ↓
只记得模糊印象
       ↓
依然能找到
       ↓
还能知道最终结论和历史变化
```

最终一句话：

> 一个零整理成本、可追溯、可长期演化的StarMem。

产品原则：

> 你负责忘记，系统负责记住。