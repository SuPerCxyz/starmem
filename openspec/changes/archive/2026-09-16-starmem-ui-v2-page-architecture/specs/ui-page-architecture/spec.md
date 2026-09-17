# ui-page-architecture Specification

## Purpose

为 StarMem 的四个主页面建立统一且角色分明的页面母版：记录页以快速捕获为核心，时间线页承担完整历史浏览，搜索页提供完整检索工作区，问记忆页提供完整 AI 记忆工作区。所有外观元素均来自 Preline UI，不引入第二套视觉体系。

## ADDED Requirements

### Requirement: 统一页面头部

每个主页面 SHALL 使用同一 `PageHeader` 结构呈现标题、可选描述与可选右侧操作，不得各自定义标题字号、间距或重复营销文案。

#### Scenario: 记录页头部
- **WHEN** 用户打开记录页
- **THEN** 显示标题「有什么需要记住的？」与描述「记录之后，StarMem 会自动整理和关联。」

#### Scenario: 时间线页头部
- **WHEN** 用户打开时间线页
- **THEN** 显示标题「时间线」与描述「按时间浏览和找回所有记录。」

#### Scenario: 搜索页头部
- **WHEN** 用户打开搜索页
- **THEN** 显示标题「搜索任何记忆」与描述「支持全文、语义、实体、时间和来源检索。」

#### Scenario: 问记忆页头部
- **WHEN** 用户打开问记忆页
- **THEN** 显示标题「问记忆」与描述「基于你的记录和来源回答，并始终附带引用。」

#### Scenario: 禁止营销型眉标
- **WHEN** 任一主页面渲染
- **THEN** 不出现全大写英文眉标（如 CAPTURE FIRST / SEARCH FIRST）

### Requirement: 统一过滤栏

时间线页与搜索页 SHALL 使用同一 `FilterBar` 组件呈现筛选控件、范围选择与结果计数，控件视觉与响应式行为一致。

#### Scenario: 时间线过滤栏
- **WHEN** 用户在时间线页使用过滤栏
- **THEN** 可设置时间范围、内容类型与来源，并显示当前结果计数

#### Scenario: 控件一致性
- **WHEN** 对比时间线页与搜索页的过滤控件
- **THEN** 两者的 select、日期输入、间距与移动端折行行为来自同一组件

### Requirement: 统一空状态

系统 SHALL 提供统一 `EmptyState` 组件，支持标题、描述、主操作、次操作与建议列表，并用于所有主页面空态。

#### Scenario: 时间线无记录
- **WHEN** 时间线没有任何 Entry
- **THEN** 显示统一空状态并给出记录入口

#### Scenario: 搜索无结果
- **WHEN** 搜索返回 0 条结果
- **THEN** 显示提示「没有找到匹配内容」并列出可操作建议：缩短关键词、切换语义搜索、放宽来源范围、移除筛选条件

#### Scenario: 搜索未执行
- **WHEN** 用户尚未发起搜索
- **THEN** 页面不显示空白，而是呈现二级内容模块

### Requirement: 统一 AI 状态

Entry 的一级视图 SHALL 只显示单一总状态，取值限定为 处理中 / 已整理 / 需复核 / 失败，全站文案与视觉一致。

#### Scenario: 状态映射
- **WHEN** Entry 的 AI 处理状态为 pending 或 retrying
- **THEN** 一级视图显示「处理中」

#### Scenario: 需复核
- **WHEN** Entry 为部分处理完成
- **THEN** 一级视图显示「需复核」

#### Scenario: 状态详情
- **WHEN** 用户点击 AI 状态
- **THEN** 打开 Drawer 展示逐项处理明细（索引 / Embedding / 分类 / 摘要 / 标签 / 实体 / Memory / Relation）与失败项重试入口

### Requirement: 记录页以捕获为核心

记录页 SHALL 以 Capture Composer 为第一任务，下方仅展示最近记录，不得呈现完整时间线浏览能力。

#### Scenario: 记录页结构
- **WHEN** 用户打开记录页
- **THEN** 页面依次呈现 PageHeader、Capture Composer、「最近记录」区块与「查看全部」入口

#### Scenario: 最近记录数量受限
- **WHEN** 记录页加载列表
- **THEN** 仅展示最近 8 条以内记录，且不显示时间范围与类型筛选器

#### Scenario: 查看全部
- **WHEN** 用户点击「查看全部」
- **THEN** 跳转到时间线页

### Requirement: 时间线页为完整历史浏览器

时间线页 SHALL 提供完整筛选、日期分组与完整分页能力。

#### Scenario: 日期分组
- **WHEN** 时间线渲染 Entry
- **THEN** 按日期分组，分组标题使用分隔线视觉而非饱和色胶囊

#### Scenario: 完整分页
- **WHEN** 用户滚动到列表底部
- **THEN** 可继续加载更早的记录

### Requirement: Entry 一级信息收敛

`EntryListItem` SHALL 在一级视图展示时间、类型、2–4 个标签、正文或摘要、AI 总状态、收藏与更多操作；SHALL NOT 默认展示 Embedding、分类、实体、关系、Prompt 版本、Worker 与 Job 明细。

#### Scenario: 默认视图
- **WHEN** Entry 出现在记录页或时间线页
- **THEN** 不直接显示逐项 AI 处理状态或 Job 标识

#### Scenario: 更多操作
- **WHEN** 用户打开 Entry 的更多菜单
- **THEN** 菜单包含复制、固定、编辑、查看历史、重新 AI 处理、删除

#### Scenario: 查看历史
- **WHEN** 用户选择「查看历史」
- **THEN** 展示该 Entry 的版本列表与差异（只读）

### Requirement: 搜索工作区

搜索页 SHALL 在未搜索、有结果、无结果三种状态下均呈现完整页面内容。

#### Scenario: 未搜索态内容
- **WHEN** 用户尚未搜索
- **THEN** 至少展示「保存的搜索」与「知识对象」两个模块，数据来自已有接口

#### Scenario: 有结果态
- **WHEN** 搜索返回结果
- **THEN** 显示结果计数与每条结果的片段、时间、来源、标签与命中类型徽标

#### Scenario: 命中类型
- **WHEN** 结果由不同检索方式命中
- **THEN** 以徽标区分精确匹配、语义匹配、实体匹配、记忆匹配

#### Scenario: 结果与时间线区分
- **WHEN** 渲染搜索结果
- **THEN** 使用检索结果布局，而非时间线 Entry 布局

### Requirement: 问记忆工作区

问记忆页 SHALL 在未提问与已回答两种状态下均呈现完整工作区，Sources SHALL 作为一级界面元素。

#### Scenario: 未提问态
- **WHEN** 用户尚未提问
- **THEN** 展示示例问题与最近提问（本地记录）

#### Scenario: 回答态桌面布局
- **WHEN** 用户提问并得到回答
- **THEN** 展示对话列与 Sources 栏，Sources 显示来源标题、时间、类型与命中片段

#### Scenario: Sources 跳转
- **WHEN** 用户点击某条来源
- **THEN** 可打开对应原始 Entry 或证据链接

#### Scenario: 移动端来源
- **WHEN** 用户在移动端查看回答
- **THEN** 通过「查看来源」按钮打开 Bottom Sheet，而非保留双栏

#### Scenario: 追问
- **WHEN** 用户在答案下方继续追问
- **THEN** 发起新的单轮提问（不保留多轮会话上下文）

### Requirement: 无虚假业务模块

页面完整度 SHALL 来自真实信息结构、空状态、结果区与来源区；SHALL NOT 新增无后端支撑的统计、评分或图表模块。

#### Scenario: 最近搜索来源
- **WHEN** 展示「最近搜索」或「最近提问」
- **THEN** 数据来自用户本机真实操作记录，不出现伪造示例数据

#### Scenario: 知识对象
- **WHEN** 展示知识对象模块
- **THEN** 数据来自已有 projects / topics / entities 接口，且文案不宣称「最近使用」
