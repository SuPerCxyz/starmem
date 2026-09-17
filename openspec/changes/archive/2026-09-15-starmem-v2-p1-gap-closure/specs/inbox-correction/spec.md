## ADDED Requirements

### Requirement: Inbox 支持人工修正

系统 SHALL 提供 `PATCH /api/v1/inbox/{job_id}` 修正导入的标题与内容类型。

#### Scenario: 修正标题

- **WHEN** 用户提交新的标题或内容类型
- **THEN** Entry 更新并追加 EntryVersion，附件与 ContentUnit provenance 保持不变

#### Scenario: 处理中

- **WHEN** 导入任务仍在处理中
- **THEN** 返回 409 且不修改数据
