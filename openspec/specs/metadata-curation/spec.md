# metadata-curation Specification

## Purpose
TBD - created by archiving change starmem-v2-p1-gap-closure. Update Purpose after archive.
## Requirements
### Requirement: AI Metadata 可人工编辑且不被覆盖

系统 SHALL 允许用户修改 Entry 的标签、类型、项目、Topic、Summary、Entity 与 Importance，并保证人工修改在 AI 重新处理时不被覆盖。

#### Scenario: 修改类型与 Summary

- **WHEN** 用户提交新的内容类型与 Summary
- **THEN** 系统写入用户来源的标记与观测，Entry 返回更新后的值

#### Scenario: 人工修改后重跑 AI

- **WHEN** 用户修改标签、实体或 Summary 后触发重新处理
- **THEN** AI 结果不得覆盖 user-locked 观测、user-confirmed 标签和 user 来源实体

#### Scenario: 非法值

- **WHEN** 用户提交超出范围的 Importance、空标签或未知项目
- **THEN** 返回 422 且不产生部分写入

### Requirement: Project/Topic/Entity 可人工管理

系统 SHALL 提供重命名、合并与排除错误归类操作，且不删除原始 Entry 与证据。

#### Scenario: 合并 Project

- **WHEN** 用户把 Project A 合并到 Project B
- **THEN** A 的观测重新指向 B，A 标记为 merged 并从默认列表隐藏，Entry 证据保留

#### Scenario: 排除错误归类

- **WHEN** 用户排除某 Project/Topic
- **THEN** 该对象从默认列表隐藏，原始 Entry 与观测不被删除

