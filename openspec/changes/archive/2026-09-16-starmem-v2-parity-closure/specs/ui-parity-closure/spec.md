## Purpose

让设计文档声明的 P0/P1 交互在 Web 端真正闭环：快速输入可键盘提交、卡片直接呈现派生结果、时间线可选任意范围、检索可切换模式并复用过滤器、Prompt Studio 可在界面内完成预览与测试。

## ADDED Requirements

### Requirement: 键盘快捷保存

Capture 文本输入 SHALL 支持 Ctrl+Enter（macOS 为 Cmd+Enter）提交保存，并保留按钮提交路径。

#### Scenario: 键盘保存
- **WHEN** 用户在文本输入框中按下 Ctrl+Enter 且内容非空
- **THEN** 系统保存该 Entry 并清空草稿

#### Scenario: 空内容
- **WHEN** 输入为空时按下 Ctrl+Enter
- **THEN** 不发起请求且显示可理解提示

### Requirement: Entry 卡片直接展示标签

Entry 卡片 SHALL 在未展开状态下直接展示标签，标签为空时不占据视觉空间。

#### Scenario: 已有标签
- **WHEN** Entry 存在 AI 或用户标签
- **THEN** 卡片直接显示标签文本

### Requirement: Entry 逐项 AI 处理状态

Entry 卡片 SHALL 展示逐项 AI 处理状态：索引、Embedding、标签、实体、Memory，失败项 SHALL 提供重试入口。

#### Scenario: 部分失败
- **WHEN** 某 Entry 的部分 AI Job 失败
- **THEN** 卡片列出失败项并可重试该任务

### Requirement: 时间线日期范围

时间线 SHALL 支持自定义起止日期筛选，并保留今天/昨天/本周/本月预设。

#### Scenario: 自定义范围
- **WHEN** 用户设置起始与结束日期
- **THEN** 时间线仅显示该范围内的 Entry

### Requirement: 搜索模式与过滤器

搜索 SHALL 允许选择全文/语义/混合模式，并支持内容类型、标签、实体、项目、主题与时间范围过滤。

#### Scenario: 切换模式
- **WHEN** 用户选择语义模式并搜索
- **THEN** 结果来自语义检索，不可用时明确提示降级

### Requirement: Saved Search 过滤器复用

Saved Search SHALL 保存并复用查询、来源范围与过滤器；重新执行时按当前数据重新检索。

#### Scenario: 复用过滤器
- **WHEN** 用户保存带过滤器的搜索并再次打开
- **THEN** 过滤器被还原并参与检索

### Requirement: Prompt Studio 交互闭环

Prompt Studio SHALL 支持查看 Preview、对 Draft 运行测试、克隆内置 Prompt、编辑 Layer 2 Task Prompt 与模型参数、管理用户自定义 Test Case。

#### Scenario: 运行 Draft 测试
- **WHEN** 用户对 Draft 运行测试
- **THEN** 显示每个 Test Case 的通过与失败结果

#### Scenario: 克隆内置 Prompt
- **WHEN** 用户克隆内置 Prompt
- **THEN** 生成可编辑的新版本，原 Production 版本保持可用

### Requirement: 全功能遍历测试

系统 SHALL 提供覆盖主要页面与按钮的全功能遍历测试，逐项验证操作后的状态变化与实际业务效果。

#### Scenario: 遍历主流程
- **WHEN** 遍历测试执行
- **THEN** Capture、Timeline、Search、Ask、Inbox、Workbench、More、Prompt Studio 的关键按钮均被执行并断言结果
