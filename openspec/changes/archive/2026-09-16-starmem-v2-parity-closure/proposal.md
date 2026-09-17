## Why

设计文档审计发现 P0 与已确认 P1 范围内仍存在未落地的行为：Ctrl/Cmd+Enter 保存、Entry 卡片标签与逐项 AI 状态、Related Entry 确定性信号、时间线日期范围、一条 Entry 多分类、Memory 生命周期闭环、Search 模式选择、Saved Search 过滤器、Prompt Studio 预览/测试/克隆/Layer 2 与模型参数编辑/自定义 Test Case。这些缺口让设计文档声明的日常使用路径不完整。

## What Changes

- Capture 支持 Ctrl/Cmd+Enter 保存，并保留按钮保存路径。
- Entry 卡片直接展示标签与逐项 AI Job 状态（索引/Embedding/标签/实体/Memory），失败可重试。
- Related Entry 增加确定性信号：共享实体、共享标签、同 Project、同 Topic、同 Error、同 Host、语义相似度，并返回命中理由。
- 时间线支持自定义起止日期，保留今天/昨天/本周/本月预设。
- 一条 Entry 支持多分类（`content_types`），保持向后兼容的单一 `content_type` 主分类。
- Memory 生命周期闭环：查看/确认/标记 expired/删除，`expired` 状态真正可写可筛选。
- Search 暴露 全文/语义/混合 模式选择，并支持类型/标签/实体/项目/主题/时间过滤。
- Saved Search 保存并复用完整过滤器。
- Prompt Studio 支持 Preview、Draft 测试、克隆内置 Prompt、编辑 Layer 2 Task Prompt 与模型参数、用户自定义 Test Case CRUD。
- 新增全功能遍历测试：逐个页面/按钮覆盖点击后的完整逻辑闭环。

## Capabilities

### New Capabilities
- `ui-parity-closure`: Capture 键盘保存、Entry 卡片标签与逐项 AI 状态、时间线日期范围、搜索模式与过滤器 UI、Saved Search 过滤器、Prompt Studio 交互闭环。
- `entry-multi-classification`: 一条 Entry 多分类及检索/展示/人工编辑行为。
- `related-entry-signals`: Related Entry 的确定性信号与命中理由。
- `memory-lifecycle-management`: Memory 查看/确认/expired/删除闭环与状态筛选。

### Modified Capabilities
- `prompt-studio`: 新增克隆、Layer 2 编辑、模型参数编辑与用户自定义 Test Case。

## Impact

- Backend：Entry 多分类迁移与模型字段、Related 信号服务、Memory 状态接口、Prompt Studio 接口扩展、Entry AI 状态接口。
- Web：Capture、EntryCard、Timeline、Search、More(Memory)、Workbench、Prompt Studio。
- Tests/Docs：后端测试、Playwright 全功能遍历、实现记录与 DEVELOPMENT_STATUS 更新。
- 明确排除：CLI、MCP、浏览器插件、External Connector、第三方导入、离线/推送/相机/语音/Passkey、P2 能力。
