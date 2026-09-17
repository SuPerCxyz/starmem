# ask-analytics Specification

## Purpose
TBD - created by archiving change starmem-v2-p1-gap-closure. Update Purpose after archive.
## Requirements
### Requirement: Ask 查询日志脱敏有界

系统 SHALL 记录脱敏后的 Ask 查询、范围、结果计数与耗时，不保存答案正文或来源内容。

#### Scenario: 执行 Ask

- **WHEN** 用户发起 Ask 请求
- **THEN** 查询日志写入脱敏查询与统计字段

#### Scenario: 敏感查询

- **WHEN** 查询包含密钥模式
- **THEN** 落库内容为脱敏结果

### Requirement: 「最近常问」Smart View

系统 SHALL 在 Smart View 中提供「最近常问」，聚合最近 30 天高频脱敏查询。

#### Scenario: 有历史查询

- **WHEN** 最近 30 天存在重复查询
- **THEN** 视图按次数降序返回聚合条目

#### Scenario: 无历史查询

- **WHEN** 没有任何查询日志
- **THEN** 视图返回空列表

