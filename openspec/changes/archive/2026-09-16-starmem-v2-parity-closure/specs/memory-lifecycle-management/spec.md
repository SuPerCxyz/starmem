## Purpose

补齐 Canonical Memory 的用户可见生命周期闭环：查看、确认、标记过期与删除，且状态变化可被筛选与追溯。

## ADDED Requirements

### Requirement: Memory 生命周期操作

系统 SHALL 支持查看 Memory 列表与详情、确认、标记 expired、删除，并保留来源证据与历史关系。

#### Scenario: 确认 Memory
- **WHEN** 用户确认某条 candidate 或 conflicted Memory
- **THEN** 该 Memory 变为 active 且不删除其证据

#### Scenario: 标记过期
- **WHEN** 用户将 Memory 标记为 expired
- **THEN** 状态变为 expired、记录过期时间，并保留原始证据

#### Scenario: 删除 Memory
- **WHEN** 用户删除 Memory
- **THEN** 状态变为 deleted，不移除 Raw Entry

#### Scenario: 状态筛选
- **WHEN** 用户按 active/superseded/conflicted/expired/deleted 过滤
- **THEN** 列表只返回对应状态
