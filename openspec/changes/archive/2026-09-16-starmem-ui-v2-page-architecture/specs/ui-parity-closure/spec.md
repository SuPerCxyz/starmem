# ui-parity-closure Specification (delta)

## MODIFIED Requirements

### Requirement: Entry 逐项 AI 处理状态

Entry 的一级视图 SHALL 只展示统一总状态（处理中 / 已整理 / 需复核 / 失败）；逐项 AI 处理状态（索引、Embedding、标签、实体、Memory 等）SHALL 移入「AI 状态」详情 Drawer。失败项 SHALL 在 Drawer 内保留重试入口。

#### Scenario: 部分失败
- **WHEN** 某 Entry 的部分 AI Job 失败
- **THEN** 一级视图显示「需复核」或「失败」，用户打开 AI 状态 Drawer 后可查看失败项并逐项重试

#### Scenario: 一级视图噪声
- **WHEN** Entry 出现在记录页或时间线页且未被展开
- **THEN** 不直接显示 Embedding、分类、实体、关系、Job 标识等逐项明细

#### Scenario: 重试能力保留
- **WHEN** 用户在 AI 状态 Drawer 中点击失败项的重试
- **THEN** 系统重新提交该 AI 步骤，且行为与迁移前一致
