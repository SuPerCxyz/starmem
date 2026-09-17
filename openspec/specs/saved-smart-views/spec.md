# saved-smart-views Specification

## Purpose
让用户可以保存常用检索条件，并通过内置 Smart View 快速打开问题、决策、TODO、失败任务和 Memory 等动态集合。
## Requirements
### Requirement: Saved Search persists reusable filters

系统 MUST 支持创建、列出、读取、更新和删除 Saved Search；每项至少保存名称、查询文本、来源范围和时间/类型/标签/实体/项目/主题过滤条件。重新执行 MUST 使用当前数据，不复制结果快照。

#### Scenario: Save a troubleshooting search

- **WHEN** 用户保存“OpenStack + 最近 30 天 + 故障”的查询
- **THEN** Saved Search 保存名称和完整过滤器，之后打开时返回当前匹配记录

#### Scenario: Delete a saved search

- **WHEN** 用户删除 Saved Search
- **THEN** 只删除查询定义，不删除任何 Entry、Memory 或来源证据

### Requirement: Smart Views have stable semantics

系统 MUST 提供稳定标识的内置 Smart View，至少覆盖问题、解决方案、TODO、决策、测试/性能、最近修改、未解决问题、新增 Memory、Conflicted Memory 和 AI Processing Failed；视图结果 MUST 遵循默认软删除和来源边界。

#### Scenario: Open AI failure view

- **WHEN** 用户打开 AI Processing Failed Smart View
- **THEN** 系统展示当前失败的 AI Job 对应 Entry，并提供进入重处理路径

#### Scenario: Open conflicted memory view

- **WHEN** 用户打开 Conflicted Memory Smart View
- **THEN** 系统只展示 Conflicted 状态 Memory 及其来源，不把历史 Memory 当作 Active 结论

