## Why

P0/P1 输入层已经能保存和检索原始内容，但自动提取的 Project、Topic、Entity、Secret 和相似内容仍缺少可观察的工作台，用户也无法把常用检索固定为可复用视图。P1 需要把这些派生信息转成可查询、可修正、可回顾的工作面，同时继续保持 Raw Entry 不可被派生数据替代。

## What Changes

- 新增 Project、Topic、Entity 统计与详情 API/Web 页面，使用既有 Observation、EntryEntity 和 Memory 证据聚合。
- 新增 Saved Search 和 Smart View，支持保存查询条件、重新执行、删除和内置问题/决策/TODO/失败任务等动态视图。
- 新增本地 Secret Detection，显示类型和位置等安全摘要，原文保持不变，远程 Chat 继续使用脱敏内容。
- 新增重复/相似 Entry 检测和“仍然保存/查看相似内容”路径，不自动合并或删除 Raw。
- 新增模型路由设置、Knowledge Summary 生成/查看和按时间范围的回顾接口。
- 在 More/Workbench 中提供上述能力的可用入口，移动端保持单列和触摸可用。

## Capabilities

### New Capabilities

- `knowledge-workbench`: Project、Topic、Entity、回顾和 Knowledge Summary 查询/详情。
- `saved-smart-views`: Saved Search 持久化和内置 Smart View。
- `safety-duplicate-detection`: 本地 Secret Detection、相似 Entry 建议和安全展示。
- `model-routing`: 按任务配置 Provider/model 路由并保留运行时 Key 边界。

### Modified Capabilities

- None. P0/P1 的 Raw、Search、Memory 和 Source 契约保持兼容；新增派生字段、查询接口和设置字段均为向后兼容扩展。

## Impact

- Backend：新增 Alembic migration、Safety Scan/Saved Search 持久化、workbench service、统计/视图/回顾/Knowledge API 和路由设置。
- Web：新增 Workbench 面板、保存搜索、Smart View、项目/主题/实体详情、相似内容和安全摘要。
- AI/Privacy：Secret Detection 在本地确定性执行；模型路由不回显 Key，Chat 发送前仍执行现有脱敏。
- Tests/Docs：覆盖聚合统计、视图持久化、重复保留、Secret 分类、路由设置、Knowledge 来源和时间回顾。
