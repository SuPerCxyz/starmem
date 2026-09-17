## 1. 基础与迁移

- [x] 1.1 新增 Alembic migration：`entries.content_types` JSONB 默认空数组
- [x] 1.2 扩展 Entry 模型与 Schema：`content_types` 读取回退 `content_type`
- [x] 1.3 多分类写入：AI/规则判定写入多分类且不覆盖用户锁定

## 2. Related Entry 确定性信号

- [x] 2.1 服务层计算共享实体/标签/Project/Topic/Error/Host 与语义相似度信号
- [x] 2.2 API 返回候选 `score` 与 `reasons` 命中理由
- [x] 2.3 前端展示命中理由并支持跳转

## 3. Entry 卡片与时间线

- [x] 3.1 Capture 支持 Ctrl/Cmd+Enter 保存与空内容提示
- [x] 3.2 卡片直接展示标签（空则不占位）
- [x] 3.3 卡片展示逐项 AI 状态（索引/Embedding/标签/实体/Memory）与失败重试
- [x] 3.4 时间线支持自定义起止日期，保留既有预设

## 4. 搜索与 Saved Search

- [x] 4.1 搜索支持全文/语义/混合模式选择与降级提示
- [x] 4.2 搜索支持类型/标签/实体/项目/主题/时间过滤
- [x] 4.3 Saved Search 保存并在复用时可还原过滤器

## 5. Memory 生命周期闭环

- [x] 5.1 新增标记 expired 接口与状态写入（保留证据）
- [x] 5.2 前端 Memory 列表支持状态筛选、确认、标记过期、删除
- [x] 5.3 测试：确认/过期/删除的状态迁移与证据保留

## 6. Prompt Studio 交互闭环

- [x] 6.1 支持克隆内置 Prompt 为可编辑 Draft
- [x] 6.2 支持编辑 Layer 2 Task Prompt 与模型参数（provider/model/temperature/top_p/max_tokens）
- [x] 6.3 支持 Preview 与 Draft 测试结果展示
- [x] 6.4 支持用户自定义 Test Case CRUD（内置用例不可删除）

## 7. 测试与文档

- [x] 7.1 后端测试覆盖多分类、Related 信号、Memory 状态、Prompt Studio 新接口、AI 状态聚合
- [x] 7.2 Playwright 全功能遍历：逐页面执行按钮并断言状态变化与业务效果
- [x] 7.3 运行 pytest、ruff check/format、Compose smoke、Web build、Playwright 并记录真实结果
- [x] 7.4 更新 README / DEVELOPMENT_STATUS / 阶段实现文档
- [x] 7.5 strict 校验并归档本 change，同步主 spec
