# StarMem v2：功能清单与产品方向

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


## 1. 产品定位

这是一个 **Capture-first、Search-first、Memory-first** 的StarMem。

目标不是做成传统笔记软件，也不是做成“AI 版 Obsidian”，而是：

> 用户只负责输入，系统负责理解、关联、整理、检索和回忆。

核心使用方式：

- 每天把大量、杂乱、没有整理过的文本直接丢进去
- 不要求标题、目录、标签、分类
- 系统自动提取摘要、主题、标签、实体、项目、问题、结论、长期记忆
- 后续既可以按关键词、时间搜索，也可以通过“模糊记忆”向大模型提问
- AI 回答必须引用原始记录
- AI 提取出的长期 Memory 可以随着后续信息更新、替代、冲突检测和演化

典型场景：

- 技术故障记录
- Shell 命令
- 配置片段
- 项目需求
- 临时想法
- 测试结果
- 性能数据
- 软件使用经验
- TODO
- 决策记录
- 网页资料
- 日志
- 图片、PDF、截图等

---

# 2. 产品核心原则

| 原则 | 要求 |
|---|---|
| Raw First | 用户原始内容永远是最高事实来源 |
| Zero Organization | 保存时不强制标题、目录、标签、分类 |
| AI Additive | AI 只能增加 metadata，不擅自修改原文 |
| Search First | 主要找资料方式是搜索，而不是浏览目录 |
| Memory ≠ Note | 原始记录和 AI 长期记忆必须分开 |
| Source Traceable | AI 所有重要答案必须能跳回原始记录 |
| Temporal | 时间是一等公民 |
| Entity Aware | 主机、项目、软件、人物、型号等是一等实体 |
| Hybrid Retrieval | 关键词、语义、实体、时间同时参与检索 |
| Self-hosted First | 数据、Embedding、LLM 都可以自己托管 |
| Replaceable AI | 不绑定某一家 LLM / Embedding 模型 |
| Never Lose Data | AI 挂掉也不能影响记录与全文搜索 |
| User Override | 人工修改优先级必须高于 AI 自动判断 |
| Re-processable | 后续可以用更好的模型重新分析历史数据 |

---

# 3. 参考社区项目

## 3.1 Memos

重点参考：

- 无标题快速记录
- 时间线优先
- 低摩擦输入
- Markdown
- 标签
- 自托管

适合借鉴：

> “先记录，再整理”的 Capture UX。

---

## 3.2 Karakeep

重点参考：

- 统一 Inbox
- Note / Link / Image / PDF
- AI 自动标签
- OCR
- 网页归档
- Full Text Search
- Semantic Search
- Hybrid Search
- CLI / stdin 输入

特别值得参考：

- 新内容自动打标签时复用历史已有标签
- 避免 AI 不断生成同义标签
- Full Text / Semantic / Hybrid 三种搜索方式

---

## 3.3 Mem0

重点参考：

- Raw Message 与 Memory 分离
- Semantic Retrieval
- Keyword Retrieval
- Entity Retrieval
- Temporal Retrieval
- Graph Memory
- Memory 更新
- 去重
- 长期事实提取

特别适合用于：

- 长期 Memory Layer
- Memory 生命周期
- 实体关系
- 时间演变

---

## 3.4 Khoj

重点参考：

- 对个人资料进行自然语言问答
- Notes / Documents RAG
- 自托管
- Personal AI
- Query → Retrieval → Answer

适合借鉴：

> “我记得以前有一次……”这种模糊提问方式。

---

## 3.5 Reor

重点参考：

- Local-first
- Semantic Search
- 自动关联相关笔记
- 自动 Related Notes
- Local Embedding

适合借鉴：

> 不要求用户维护所有 backlinks，由系统自动发现相关内容。

---

## 3.6 Trilium

重点参考：

- Attributes
- Saved Search
- Note Versioning
- Relations
- Metadata
- 大规模个人知识库管理

适合借鉴：

- 动态视图
- 属性体系
- 版本历史

---

## 3.7 Anytype / Logseq / Obsidian 生态

重点参考：

- Object
- Relation
- Backlink
- Knowledge Graph
- Properties
- Local-first

不建议直接照搬：

- 大量人工目录
- 大量人工链接
- 保存前先分类
- 复杂手工知识管理流程

---

# 4. P0：第一版必须实现

P0 的目标：

> 做出一个真正可以每天使用的“StarMem”。

---

# 5. 快速输入

必须支持：

- 首页巨大输入框
- 无标题保存
- 标题可选
- Markdown
- Code Block
- 多行文本
- 大段日志
- Ctrl+Enter 保存
- 自动保存草稿
- 自动记录创建时间
- 自动记录更新时间
- 原始文本永久保存
- 编辑
- 软删除
- Pin
- 收藏
- 标签展示
- AI 状态展示

保存时禁止强制要求：

- 标题
- 目录
- 项目
- 标签
- 分类

---

# 6. 时间线

首页主要展示 Timeline：

```text
今天

13:42
node-3903 multipath 出现 undef running...
#Storage #multipath #iSCSI

12:17
Codex ssh 执行复杂 shell 经常出现引号展开问题...
#Codex #SSH #问题

10:25
Lumen 网关需要支持 Response API...
#Lumen #需求
```

功能：

- 按天分组
- 无限滚动
- 日期跳转
- 今天
- 昨天
- 本周
- 本月
- 指定时间范围
- Pin
- 收藏
- 标签
- 内容类型
- 快速编辑
- 展开原文
- 查看 AI Metadata
- 查看关联内容

---

# 7. AI Enrichment Pipeline

每条 Entry 保存后异步执行：

```text
Raw Entry
   ↓
AI Enrichment
   ├─ 内容类型
   ├─ 摘要
   ├─ 标签
   ├─ 实体
   ├─ 项目
   ├─ 主题
   ├─ 时间信息
   ├─ 关键结论
   ├─ 问题
   ├─ 解决方案
   └─ 长期 Memory
```

注意：

> AI Metadata 永远不能覆盖 Raw Entry。

---

# 8. 自动内容分类

建议初始支持：

- 普通记录
- 故障排查
- 问题
- 解决方案
- 命令
- 配置
- 代码
- 项目需求
- 想法
- 决策
- TODO
- 参考资料
- 知识
- 测试结果
- 性能数据
- 会议 / 沟通
- 链接
- 日志

允许：

- 一条 Entry 多分类

---

# 9. 自动标签

AI 自动生成标签，但必须避免无限产生同义标签。

推荐流程：

```text
新记录
 ↓
寻找 Top N 相似记录
 ↓
获取历史已有标签
 ↓
优先复用已有标签
 ↓
没有合适标签
 ↓
才允许创建新标签
```

标签来源区分：

- User Created
- User Confirmed
- AI Generated

优先级：

```text
User Created
>
User Confirmed AI
>
AI Generated
```

---

# 10. 实体识别

自动提取实体。

建议实体类型：

- Host
- IP
- Domain
- Project
- Software
- Service
- Model
- Hardware
- Company
- Person
- Location
- Error
- Command
- API
- File
- Repository
- Product
- Protocol
- Storage
- Cluster
- VM
- Container

例如：

```text
node-3903 上 iscsi session 没有正常清理，
导致 multipath 出现 undef running。
```

自动提取：

```text
Host:
node-3903

Technology:
iSCSI
multipath

Domain:
Storage

Problem:
stale session
```

---

# 11. 全文搜索

P0 必须实现传统 Full Text Search。

用于搜索：

- 精确关键词
- 完整短语
- Hostname
- IP
- UUID
- WWN
- Error Code
- Command
- File Path
- Model
- API
- Domain
- 日期

要求：

- 命中高亮
- 时间过滤
- 类型过滤
- 标签过滤
- 实体过滤

原因：

> 向量检索不能替代精确搜索。

例如 WWN、UUID、错误码必须依赖全文搜索。

---

# 12. Semantic Search

支持自然语言和模糊记忆搜索。

例如：

```text
那个 iSCSI 没清干净导致磁盘异常的问题
```

即使原始记录中没有这句话，也应该找到：

```text
旧 session 未清理
multipath undef running
```

---

# 13. Hybrid Search

默认搜索方式必须是 Hybrid Search。

推荐评分来源：

```text
Final Score =
    Keyword Score
  + Semantic Score
  + Entity Score
  + Tag Score
  + Temporal Score
  + Recency Score
  + Importance Score
```

之后：

```text
Candidate Retrieval
↓
Reranker
↓
Final Results
```

UI 搜索模式：

```text
● 智能 Hybrid
○ 全文
○ 语义
```

默认：

> 智能 Hybrid。

---

# 14. 时间理解

搜索和问答必须理解：

- 今天
- 昨天
- 上周
- 上个月
- 前几天
- 7 月份
- 今年夏天
- 前段时间
- 最近
- 之前
- 第一次
- 最新一次
- 去年
- 某个具体月份

例如：

```text
我前段时间测试 V100 的结果
```

检索应该同时利用：

```text
Semantic
+
Entity=V100
+
Temporal Bias
```

---

# 15. 自然语言问答

用户可以直接问：

```text
我以前有没有遇到 multipath undef？
```

或者：

```text
好像有一次是 iscsi 没清干净，最后怎么解决的？
```

推荐流程：

```text
Query
 ↓
Query Understanding
 ↓
Time Intent
Entity
Keyword
Semantic
 ↓
Hybrid Retrieval
 ↓
Rerank
 ↓
Context Build
 ↓
LLM
 ↓
Answer
```

---

# 16. AI 回答必须引用来源

任何重要答案都必须引用：

- 原始 Entry
- 日期
- 时间
- 来源内容

例如：

```text
你在 2026-09-11 记录过类似问题。

node-3903 的 multipath 出现 undef running，
当时确认与废弃 iSCSI session 没有清理有关。

最终处理：
1. disablequeueing
2. 清理异常 path
3. 清理废弃 session

来源：
[2026-09-11 14:23 · 查看原始记录]
```

禁止：

> AI 推测和用户真正记录过的内容混在一起而无法区分。

---

# 17. Memory Layer

Entry 和 Memory 必须分离。

例如原始 Entry：

```text
测试下来 V100 设置 150W 性能下降很小，
所以之后统一保持 150W。
```

生成 Memory：

```text
subject: V100
predicate: power_limit
value: 150W

text:
V100 当前长期功耗限制为 150W

source:
entry_12345
```

以后用户问：

```text
V100 功耗多少？
```

可以优先命中 Memory。

---

# 18. Memory 生命周期

Memory 状态建议：

- Active
- Superseded
- Conflicted
- Expired
- Deleted

例如：

```text
6 月：
V100 设置 200W

8 月：
V100 改成 180W

9 月：
V100 最终固定 150W
```

系统应该形成：

```text
V100 power_limit

200W
↓ superseded

180W
↓ superseded

150W
● current
```

历史仍然全部保留。

---

# 19. Memory 冲突检测

例如历史：

```text
Lumen 默认端口 = 8080
```

新内容：

```text
Lumen 默认端口改成 8081
```

系统应该提示或自动判断：

```text
旧 Memory：
8080

新 Memory：
8081

建议：
旧 Memory → Superseded
新 Memory → Active
```

对于低置信度情况：

- 不自动覆盖
- 标记 Conflicted
- 提示用户确认

---

# 20. Related Entries

每条 Entry 自动显示关联记录：

```text
相关记录

91% 旧 WWN 残留问题
86% multipath path 清理脚本
78% os-brick detach 问题
```

关联信号可以来自：

- Semantic Similarity
- Shared Entities
- Shared Tags
- Same Project
- Same Topic
- Same Error
- Same Host

---

# 21. 技术内容特殊处理

必须识别：

- Shell
- Python
- YAML
- JSON
- Dockerfile
- docker-compose
- systemd
- SQL
- Log
- Config
- XML
- TOML
- INI

代码块和命令不能被错误切碎。

例如：

```bash
iscsiadm -m node \
-T iqn.xxx \
-o delete
```

搜索：

```text
之前删除 iscsi node 的命令
```

应该直接返回完整代码块。

---

# 22. AI Processing 状态

Entry 卡片显示：

```text
✓ 已索引
✓ 已生成 Embedding
✓ 已提取标签
✓ 已提取实体
✓ 已生成 Memory
```

失败：

```text
⚠ AI Processing Failed
[重新处理]
```

即使 AI 处理失败：

> Raw Entry 仍然必须成功保存。

---

# 23. AI Metadata 可编辑

用户可以手工修改：

- 标签
- 类型
- 项目
- Topic
- Summary
- Entity
- Memory
- Importance

人工修改后：

> AI 不允许再次自动覆盖。

---

# 24. AI 重新处理

支持：

- 重新分析此 Entry
- 重新生成摘要
- 重新生成标签
- 重新提取实体
- 重新生成 Memory
- 重新生成 Embedding
- 重新建立 Related Entries

管理员功能：

- 批量重新分析
- 全库重新 Embedding
- 模型升级后重新处理

---

# 25. P1：多类型输入

支持：

- URL
- Image
- Screenshot
- PDF
- TXT
- Markdown
- JSON
- YAML
- Log
- 文件附件
- 网页正文
- OCR

统一视为：

> Entry。

---

# 26. 网页保存

粘贴 URL 后：

```text
URL
↓
抓正文
↓
保存网页快照
↓
标题
↓
摘要
↓
标签
↓
Entity
↓
Embedding
↓
Memory Extraction
```

要求：

- 原 URL 保存
- 正文保存
- 网页失效后仍可查看历史快照
- AI 自动摘要
- 自动标签
- 自动实体提取

---

# 27. 图片 / OCR

图片支持：

- OCR
- 图片描述
- 截图文本识别
- 图片自动标签
- 图片内容搜索
- 图片作为来源参与问答

---

# 28. PDF

支持：

- PDF 上传
- 文本提取
- 页码保留
- Chunk
- Semantic Search
- Full Text Search
- 问答
- 回答引用具体页码

---

# 29. Inbox

提供 Inbox 页面。

状态：

- New
- Processing
- Processed
- Failed

用途：

- 查看最近输入
- 查看 AI 处理失败
- 手工修正分类
- 重新处理

注意：

> Inbox 不是“待用户整理”。

---

# 30. Project 自动聚类

系统自动发现 Project：

```text
OpenStack
Lumen
Talea
GPU
Local LLM
HomeLab
```

用户可以：

- 手工确认
- 合并 Project
- 重命名
- 排除错误归类

保存时不要求选择 Project。

---

# 31. Topic 自动聚类

系统自动形成 Topic：

```text
OpenStack
 ├─ Cinder
 ├─ Nova
 ├─ Ironic
 └─ Storage

AI
 ├─ Codex
 ├─ Lumen
 ├─ Local LLM
 └─ GPU
```

Topic 是动态视图，不是强制目录。

---

# 32. Project 页面

例如：

```text
Lumen
─────────────────

记录       134
Memory      27
决策         8
问题        13
TODO         5

最近活动
关键 Memory
重要决策
未解决问题
相关实体
最近记录
```

---

# 33. Entity 页面

例如点击：

```text
node-3903
```

显示：

```text
node-3903

类型：
Host

首次出现：
2026-06-12

最近出现：
2026-09-15

相关：
multipath
iSCSI
Cinder
os-brick

相关记录：
37

发生过的问题：
12

解决方案：
9
```

---

# 34. Saved Search

例如：

```text
OpenStack + 最近30天 + 故障
```

保存为：

```text
最近 OpenStack 故障
```

---

# 35. Smart View

系统内置动态视图：

- 所有问题
- 所有解决方案
- 所有 TODO
- 所有决策
- 所有测试结果
- 所有性能记录
- 最近修改
- 最近常问
- 未解决问题
- 新增 Memory
- Conflicted Memory
- AI Processing Failed

---

# 36. 回顾

支持自然语言或系统自动回顾：

```text
今天记录了什么？
```

```text
这周解决了哪些问题？
```

```text
最近有哪些 TODO？
```

```text
最近有哪些新的项目决策？
```

```text
一个月前的今天记录了什么？
```

---

# 37. Knowledge Summary

同一主题大量 Entry 可以自动生成 Derived Knowledge。

例如：

```text
Multipath 残留清理经验

常见原因
处理流程
风险
相关命令
历史案例
```

注意：

> Knowledge Summary 是 Derived Data，不能替代 Raw Entry。

---

# 38. 重复内容检测

例如新保存：

```text
V100 设置 150W
```

已有：

```text
V100 最后固定 150W
```

提示：

```text
检测到高度相似内容
```

操作：

- 仍然保存
- 合并 Memory
- 查看相似内容

默认：

> Raw Entry 仍然保存。

因为重复记录本身包含时间信息。

---

# 39. Secret Detection

自动检测：

- Password
- Token
- API Key
- AK / SK
- Private Key
- Cookie
- Authorization Header
- Database Password
- SSH Key

处理方式：

- 正常保存
- 脱敏显示
- 禁止发送云端 LLM
- 仅本地模型处理

---

# 40. Model Routing

支持 OpenAI-compatible API。

模型可以拆开：

```text
Classification Model
Summary Model
Memory Model
Chat Model
Embedding Model
Reranker
OCR Model
```

不同任务可以使用不同模型。

---

# 41. Local AI

支持：

```text
Embedding → Local

Classification → Local

Memory Extraction → Local

RAG Chat → Local / Remote

OCR → Local
```

建议兼容：

- OpenAI-compatible
- Ollama
- vLLM
- llama.cpp Server
- Custom Endpoint

---

# 42. API

建议 P1 提供：

```http
POST /entries
GET  /entries
GET  /entries/{id}

GET  /search
POST /ask

GET  /memories
GET  /entities
GET  /topics
GET  /projects

POST /reprocess
```

---

# 43. CLI

建议支持：

```bash
starmem add "..."
```

```bash
dmesg | starmem add --type log
```

```bash
starmem search multipath
```

```bash
starmem ask "之前那个 iscsi 问题怎么处理"
```

```bash
starmem get <id>
```

---

# 44. MCP Server

建议 P1 即支持。

提供工具：

```text
starmem_search
starmem_get
starmem_add
starmem_ask
starmem_find_related
starmem_get_entity
starmem_get_project
```

用途：

- Codex
- OpenCode
- Claude Code
- 其他 AI Agent

都可以直接访问个人长期记忆库。

这会让系统成为：

> StarMem Long-term Agent Memory Backend。

---

# 45. 浏览器插件

浏览器提供：

```text
Save to Memory
```

支持：

- 保存网页
- 保存选中文字
- 保存网页 + 注释
- 保存截图
- 保存链接

---

# 46. PWA / 手机分享

支持：

- PWA
- 手机浏览器
- Share to Memory

可以从手机分享：

- 网页
- 文本
- 图片
- 文件

直接进入个人 Memory Inbox。

---

# 47. Import / Export

Export：

- Markdown
- JSON
- JSONL
- ZIP

Import：

- Memos
- Obsidian
- Trilium
- Notion
- Karakeep
- ChatGPT Export
- Claude Export
- Markdown Folder

---

# 48. Version History

每次修改 Entry：

```text
V1
V2
V3
```

都保留。

支持：

- 查看历史
- Diff
- 恢复旧版本

---

# 49. Backup

必须支持：

- 数据库备份
- 附件备份
- Embedding 可重新生成
- 一键导出
- 一键恢复
- Docker Volume Backup

原则：

> 原始数据价值高于应用本身。

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


# 50. P2：高级能力

P2 再做：

- Knowledge Graph UI
- Relation Graph
- Topic Evolution
- Project Evolution
- Advanced Memory Consolidation
- 自动知识归并
- 主动提醒旧知识
- Agent 主动读取 Memory
- 多数据源同步
- 邮件导入
- IM 导入
- GitHub Issue / PR 导入
- Calendar Event 导入
- 自动每日总结
- 自动每周总结
- Memory Quality Score
- Knowledge Gap Detection
- Long-term Trend Analysis

---

# 51. Knowledge Graph

底层关系先设计好：

```text
Entry
 ├─ mentions → Entity
 ├─ belongs_to → Topic
 ├─ belongs_to → Project
 ├─ relates_to → Entry
 ├─ produces → Memory
 ├─ source_of → Knowledge
 └─ supersedes → Memory
```

P2 再做 Graph UI。

禁止：

> 第一版投入大量时间做漂亮但低价值的知识蜘蛛网。

---

# 52. AI 自动发现隐含关系

例如：

```text
A：
multipath undef

B：
旧 iSCSI session

C：
os-brick detach

D：
WWN 残留
```

AI 自动发现：

```text
可能共同主题：
Storage stale state cleanup
```

形成：

```text
Related Cluster
```

这比普通 Graph View 更有实际价值。

---

# 53. 推荐一级导航

建议第一版尽量简单：

```text
┌────────────────────────┐

  ＋ 记录

  ◉ 时间线

  ⌕ 搜索

  ✦ 问记忆

  ───────────

  Topics
  Projects
  Entities

  ───────────

  设置

└────────────────────────┘
```

---

# 54. 首页

最重要的元素只有：

```text
┌─────────────────────────────────────────────┐
│                                             │
│   有什么需要记住的？                         │
│                                             │
│                                             │
│                                   保存 ⏎    │
└─────────────────────────────────────────────┘
```

核心理念：

> 用户不需要考虑“这东西应该放哪”。

---

# 55. 明确不做

第一阶段不要做：

| 暂时不做 | 原因 |
|---|---|
| 复杂目录树 | 与零整理理念冲突 |
| 强制标题 | 增加记录摩擦 |
| 保存前选分类 | 增加摩擦 |
| 保存前选项目 | 增加摩擦 |
| 复杂块编辑器 | 不是核心竞争力 |
| 协同编辑 | 单用户不需要 |
| 团队权限 | 不需要 |
| 评论 | 不需要 |
| Kanban | 不是核心 |
| Calendar 管理 | 不是日历软件 |
| AI 自动修改原文 | 禁止 |
| Graph 作为主要 UI | 容易华而不实 |
| 纯向量搜索 | 检索质量不够 |
| 完全依赖 LLM | AI 挂了仍应可用 |
| 自动删除历史 Memory | 必须保留演变过程 |

---

# 56. 最终优先级表

| 功能 | P0 | P1 | P2 |
|---|:---:|:---:|:---:|
| 快速文本记录 | ✅ | | |
| 时间线 | ✅ | | |
| Markdown / Code | ✅ | | |
| 全文搜索 | ✅ | | |
| Semantic Search | ✅ | | |
| Hybrid Search | ✅ | | |
| AI 自动摘要 | ✅ | | |
| AI 自动标签 | ✅ | | |
| AI 内容分类 | ✅ | | |
| Entity 提取 | ✅ | | |
| Memory 提取 | ✅ | | |
| 自然语言问答 | ✅ | | |
| 引用原始来源 | ✅ | | |
| 时间过滤 | ✅ | | |
| Related Entry | ✅ | | |
| Memory 生命周期 | ✅ | | |
| 修改 / 删除 | ✅ | | |
| AI 任务重试 | ✅ | | |
| Docker 部署 | ✅ | | |
| URL | | ✅ | |
| 图片 | | ✅ | |
| PDF | | ✅ | |
| OCR | | ✅ | |
| 网页归档 | | ✅ | |
| Project 自动聚类 | | ✅ | |
| Topic 页面 | | ✅ | |
| Entity 页面 | | ✅ | |
| 冲突检测 | | ✅ | |
| 重复检测 | | ✅ | |
| Knowledge Summary | | ✅ | |
| Saved Search | | ✅ | |
| Smart View | | ✅ | |
| 回顾 | | ✅ | |
| API | | ✅ | |
| CLI | | ✅ | |
| MCP | | ✅ | |
| 浏览器插件 | | ✅ | |
| iOS Home Screen / PWA 基础 | ✅ | | |
| Secret Detection | | ✅ | |
| Local LLM | | ✅ | |
| Import / Export | | ✅ | |
| 知识图谱 UI | | | ✅ |
| Topic Evolution | | | ✅ |
| 高级 Memory Consolidation | | | ✅ |
| 多数据源同步 | | | ✅ |
| iOS 移动端完整支持 | ✅ | | |
| iOS 主屏幕 Web App | ✅ | | |
| Source / ContentUnit 架构 | ✅ | | |
| External Corpus Connector | | ✅ | |
| 大规模异步 Ingestion | | ✅ | |
| Prompt Registry | ✅ | | |
| Prompt Studio 基础 | ✅ | | |
| User Instructions | ✅ | | |
| Prompt Versioning | ✅ | | |
| Prompt Golden Dataset | ✅ | | |
| Memory Salience | ✅ | | |
| Memory Reconcile | ✅ | | |
| Reconcile 并发保护 | ✅ | | |
| Prompt 高级完整编辑 | | ✅ | |
| Agent 主动调用记忆 | | | ✅ |
| 主动提醒旧知识 | | | ✅ |

---

# 57. 推荐产品组合思想

整体可以参考：

```text
Memos
  → Capture UX

Karakeep
  → Inbox / AI Tag / Hybrid Search / Web Archive

Mem0
  → Memory Pipeline / Temporal / Entity / Graph

Khoj
  → Natural Language QA

Reor
  → Related Notes

Trilium
  → Metadata / Saved Search / Versioning

Anytype
  → Object / Relation
```

但不应该整体复制任何一个项目。

你的目标场景是：

```text
大量杂乱技术信息
        ↓
完全不想整理
        ↓
系统自动理解
        ↓
几个月以后只凭模糊印象
        ↓
依然能够找回来
        ↓
AI 知道最终结论以及变化历史
```

---

# 58. 最终一句话定位

> 一个零整理成本的StarMem。

或者更产品化一点：

> 你负责忘记，系统负责记住。

---

# 59. 后续建议

下一阶段应该继续输出：

1. 完整 PRD
2. P0 页面结构
3. 数据库表设计
4. Entry / Memory / Entity / Topic / Project 数据模型
5. AI Enrichment Pipeline
6. Chunk 策略
7. Embedding 策略
8. Hybrid Search 算法
9. Reranker
10. Query Understanding
11. Memory 生命周期
12. Memory Conflict Detection
13. MCP Server 设计
14. REST API 设计
15. Docker Compose 架构
16. 前端技术栈
17. 后端技术栈
18. Worker / Queue 架构
19. 模型路由
20. P0 验收标准

完成这些后即可形成一份可以直接交给 Codex 执行的项目实现规格。