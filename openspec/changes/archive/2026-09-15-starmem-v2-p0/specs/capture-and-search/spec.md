## Purpose

让用户可以不做任何预分类就可靠保存长期记录，并通过精确、语义和混合检索在桌面与移动端找回原始证据。

## ADDED Requirements

### Requirement: Raw entry capture is independent of AI
系统 MUST 在用户提交有效原文后立即持久化 Raw Entry，并在 AI、Embedding、Reranker、Redis 或 Worker 不可用时仍返回保存成功。Raw Entry MUST 保留用户原文，不得被 AI 派生数据覆盖。

#### Scenario: Save while AI providers are unavailable
- **WHEN** 用户提交普通文本且所有 AI Provider 不可用
- **THEN** Entry 被保存并出现在 Timeline，全文搜索可以命中，AI Job 被记录为失败或可重试状态

#### Scenario: Save long technical content
- **WHEN** 用户提交超过 20,000 字符的日志、Markdown、JSON、YAML 或 Shell 内容
- **THEN** 原文逐字保存，页面可以展开查看，代码块和配置块不被截断或重排

### Requirement: Entries support optional metadata and safe lifecycle operations
系统 MUST 支持可选标题、内容格式/类型、Pin、Favorite、Importance、创建/更新时间、编辑和软删除；保存时不得强制标题、标签、项目或分类。

#### Scenario: Capture without organization fields
- **WHEN** 用户只填写原文而不填写标题、标签、项目或分类
- **THEN** 系统成功保存 Entry 并使用创建时间作为 Timeline 信息

#### Scenario: Soft delete and default visibility
- **WHEN** 用户删除 Entry
- **THEN** Entry 被标记为软删除，默认 Timeline 和 Search 隐藏它，但原始数据仍可恢复

### Requirement: Entry edits preserve version history
系统 MUST 为每次用户对 Raw Entry 的修改创建不可变 EntryVersion，并支持查看、Diff 和恢复历史版本；AI 不得创建或伪造 Raw Entry 版本。

#### Scenario: Edit an entry three times
- **WHEN** 用户连续修改同一 Entry 三次
- **THEN** 当前内容正确，三个历史版本均可查看和比较，并可恢复任意历史版本

### Requirement: Timeline supports time-oriented navigation
系统 MUST 以时间倒序显示 Entry，按日期分组，支持 cursor 分页/无限加载、今天、昨天、本周、本月、日期范围、Pin、Favorite、快速编辑、原文、AI Metadata、关联 Entry 和 Memory。

#### Scenario: Timeline groups entries by date
- **WHEN** 用户创建跨多个日期的 Entry 并打开 Timeline
- **THEN** Entry 按日期分组且每组内按时间倒序显示，继续加载不会重复或遗漏记录

### Requirement: Full-text search handles technical identifiers
系统 MUST 提供全文搜索、短语/片段匹配、时间/类型/标签/实体/项目/主题过滤和命中高亮，并对 IP、UUID、WWN、Hostname、错误码、路径、命令、域名和模型标识符提供精确匹配优先级。

#### Scenario: Exact WWN outranks semantic matches
- **WHEN** 用户搜索完整 WWN，且库中同时存在语义相近但未包含该 WWN 的 Entry
- **THEN** 包含完整 WWN 的 Entry 排在首位并高亮命中字符串

### Requirement: Semantic and hybrid search are replaceable-provider features
系统 MUST 支持 Chunk 级语义检索和默认 Hybrid 检索。Hybrid MUST 合并全文与向量候选，权重可配置；精确标识符命中 MUST 显著高于单纯语义相似度。无 Embedding Provider 时全文搜索仍可用，并明确返回语义能力不可用状态。

#### Scenario: Semantic recall of paraphrased content
- **WHEN** Entry 包含“旧 iscsi session 没有清理导致 multipath 路径残留”，用户搜索“之前磁盘路径因为旧连接没释放的问题”
- **THEN** 原 Entry 进入前五名并返回匹配 Chunk、相似度和摘要片段

#### Scenario: Hybrid ranking chooses the causal entry
- **WHEN** 同时存在 iscsi 清理、iscsi 登录配置和“multipath undef 由旧 iscsi session 残留造成”三条记录，用户搜索“multipath undef iscsi”
- **THEN** 因果记录排在首位

### Requirement: Search results preserve evidence context
搜索结果 MUST 返回 Entry、命中 ContentUnit/Chunk、来源信息、时间、匹配原因、分数和可用于跳转原文的标识。

#### Scenario: Open a search source
- **WHEN** 用户点击搜索结果的来源
- **THEN** 系统打开对应 Raw Entry，并定位或高亮命中原文片段
