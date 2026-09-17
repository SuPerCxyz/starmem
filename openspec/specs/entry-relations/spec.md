# entry-relations Specification

## Purpose
TBD - created by archiving change starmem-v2-p1-gap-closure. Update Purpose after archive.
## Requirements
### Requirement: Entry 相关记录可读取

系统 SHALL 提供认证的 `GET /api/v1/entries/{entry_id}/relations`，返回该 Entry 的出边与入边关系。

#### Scenario: 已存在 AI 关系

- **WHEN** 某 Entry 已通过 `relation_build` 写入 Relation
- **THEN** 接口返回关系类型、置信度、来源、方向，以及可跳转的目标 Entry 摘要

#### Scenario: 无关系

- **WHEN** Entry 不存在任何关系
- **THEN** 接口返回空列表而不是错误

#### Scenario: Entry 不存在

- **WHEN** 请求的 Entry 已被删除或不存在
- **THEN** 接口返回 404

