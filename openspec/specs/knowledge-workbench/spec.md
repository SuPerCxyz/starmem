# knowledge-workbench Specification

## Purpose
让用户能够从自动派生的 Project、Topic、Entity、Memory 和原始记录中获得可解释的工作台、Knowledge Summary 和时间回顾，而无需手工维护目录关系。
## Requirements
### Requirement: Project, topic and entity views are queryable

系统 MUST 提供 Project、Topic、Entity 列表和详情查询，返回名称、类型、首次/最近出现时间、相关 Entry 数、Memory 数和可解释的相关对象；缺少派生数据时 MUST 返回空统计而不是创建虚假关系。

#### Scenario: Open an entity detail

- **WHEN** 用户打开一个已被 EntryEntity 提取的 Host/Service Entity
- **THEN** 系统显示其类型、出现时间、相关记录、相关 Memory 和可用的相关实体

#### Scenario: View an unclassified project

- **WHEN** Project 尚未被任何 Observation 关联
- **THEN** Project 列表不虚构记录，详情显示零统计并保留可重新处理入口

### Requirement: Knowledge summaries remain derived and sourced

系统 MUST 支持按 Project、Topic 或时间范围生成和查看 Knowledge Summary；每个 Summary MUST 记录来源 Entry/Memory 标识、生成范围和 derived 状态，且不得替代或删除 Raw Entry/Atomic Memory。

#### Scenario: Generate a project summary

- **WHEN** 用户为某 Project 请求 Summary
- **THEN** 系统生成包含来源记录、关键观察和 Active Memory 的可重建 Summary，并可跳转来源 Entry

#### Scenario: Regenerate a stale summary

- **WHEN** 用户重新生成已有范围的 Summary
- **THEN** 系统更新 Derived Knowledge 和来源元数据，不修改原始记录或 Memory 生命周期

### Requirement: Time review is bounded and evidence based

系统 MUST 支持按今天、最近七天、最近三十天或自定义日期范围回顾记录、问题、决策、TODO、Memory 和处理失败项；响应 MUST 返回统计和有限来源列表。

#### Scenario: Review the current week

- **WHEN** 用户请求本周回顾
- **THEN** 系统按时间范围返回新增记录数、问题/决策/待办摘要、Memory 变化和可跳转的代表性来源

