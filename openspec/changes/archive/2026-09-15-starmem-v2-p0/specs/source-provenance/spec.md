## Purpose

建立统一的来源、检索单元和证据追踪模型，使 Native Entry 与未来外部语料库能够共享搜索、Memory 和引用链路而无需重构核心数据模型。

## ADDED Requirements

### Requirement: Native content has a built-in source
系统 MUST 创建并使用名为 `StarMem Native` 的内置 Source；Native Entry 保存后 MUST 关联 Source 并生成至少一个 ContentUnit。

#### Scenario: Persist a native entry unit
- **WHEN** 用户保存 Native Entry
- **THEN** Entry 关联 `StarMem Native`，ContentUnit 保存原文、类型、顺序、事件时间和可检索字段

### Requirement: External content uses generic read-only source models
系统 MUST 通过 Source、External Item 和 ContentUnit 表达外部数据，不得向 Entry 增加特定外部系统字段；外部原始内容在 StarMem 中默认为只读快照。

#### Scenario: Create an external fixture
- **WHEN** 测试 Fixture 创建一个 External Source 和 External Item
- **THEN** 系统可以生成 ContentUnit 并建立索引，但不能通过 StarMem 修改外部原始内容

### Requirement: Provenance is available for every search and answer source
Search 和 Ask 的每个来源 MUST 能够表示 Source、External Item（若存在）、外部原始 ID/URL/时间、StarMem 导入时间、命中 ContentUnit 和证据片段。

#### Scenario: Cite native and external evidence
- **WHEN** Ask 同时检索 Native Entry 和 External Item
- **THEN** 来源列表明确区分两种 Source，并分别显示原始标识、时间、命中片段和可用跳转

### Requirement: Search and Ask support source scope
系统 MUST 支持全部、仅我的记录、仅外部知识库和指定 Source 的 Search Scope，且 Search 与 Ask 使用同一套来源过滤语义。

#### Scenario: Restrict search to external knowledge
- **WHEN** 用户选择“仅外部知识库”并搜索关键词
- **THEN** 结果不包含 Native Entry，所有结果的 Source Attribution 均为外部 Source

### Requirement: Ingestion foundations are idempotent and asynchronous-ready
系统 MUST 为未来外部导入保留 external_id、external_updated_at、content_hash、sync_cursor、last_synced_at、Job 状态/重试和幂等字段，并定义 discover/fetch/normalize/get_cursor 的 Adapter Contract；P0 不实现具体 Connector。

#### Scenario: Repeat an external snapshot import
- **WHEN** 同一个 Source 以相同 external_id 和 content_hash 重复提交 Fixture
- **THEN** 系统不创建重复 External Item 或 ContentUnit，并保留同步状态
