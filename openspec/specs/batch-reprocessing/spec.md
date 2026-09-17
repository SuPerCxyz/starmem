# batch-reprocessing Specification

## Purpose
TBD - created by archiving change starmem-v2-p1-gap-closure. Update Purpose after archive.
## Requirements
### Requirement: 有界批量重处理

系统 SHALL 提供批量重处理接口，支持显式 Entry ID 列表或过滤器，单次上限 200 条。

#### Scenario: 按过滤器批量重处理

- **WHEN** 用户按 source_scope、日期或 content_type 提交批量重处理
- **THEN** 系统创建新 generation 的派生任务并返回 submitted/failed 计数

#### Scenario: 超出上限

- **WHEN** 请求条目数超过 200
- **THEN** 返回 422 且不创建任何任务

### Requirement: 全库 Embedding 重建入口

系统 SHALL 提供触发全库 Embedding 重建的维护入口，且不复制或删除原始 Entry。

#### Scenario: 触发重建

- **WHEN** 用户调用维护接口
- **THEN** 系统排队重建任务并返回受理结果

