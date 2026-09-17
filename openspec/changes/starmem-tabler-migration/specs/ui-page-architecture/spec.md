## MODIFIED Requirements

### Requirement: 统一页面头部

每个主页面 SHALL 使用 Tabler 官方 `page-header` / `page-header d-print-none` 结构呈现标题、可选描述、breadcrumb 与可选右侧操作，不得各自定义标题字号、间距或重复营销文案。

#### Scenario: 记录页头部
- **WHEN** 用户打开记录页
- **THEN** 显示标题「有什么需要记住的？」与描述「记录之后，StarMem 会自动整理和关联。」并使用 Tabler page-header hierarchy

#### Scenario: 时间线页头部
- **WHEN** 用户打开时间线页
- **THEN** 显示标题「时间线」与描述「按时间浏览和找回所有记录。」并使用同一 Tabler page-header hierarchy

#### Scenario: 搜索页头部
- **WHEN** 用户打开搜索页
- **THEN** 显示标题「搜索任何记忆」与描述「支持全文、语义、实体、时间和来源检索。」并使用同一 Tabler page-header hierarchy

#### Scenario: 问记忆页头部
- **WHEN** 用户打开问记忆页
- **THEN** 显示标题「问记忆」与描述「基于你的记录和来源回答，并始终附带引用。」并使用同一 Tabler page-header hierarchy

#### Scenario: 禁止营销型眉标
- **WHEN** 任一主页面渲染
- **THEN** 不出现全大写英文眉标，页面标题层级来自 Tabler 官方页面头部 class

### Requirement: 统一过滤栏

时间线页与搜索页 SHALL 使用 Tabler 官方 `form-select`、`form-control`、`input-group`、`btn`、`dropdown` 和 `card`/`toolbar` 组合呈现筛选控件、范围选择与结果计数；控件视觉与响应式行为来自同一官方组合。

#### Scenario: 时间线过滤栏
- **WHEN** 用户在时间线页使用过滤栏
- **THEN** 可设置时间范围、内容类型与来源，并显示当前结果计数

#### Scenario: 控件一致性
- **WHEN** 对比时间线页与搜索页的过滤控件
- **THEN** 两者的 select、日期输入、按钮与响应式布局均使用 Tabler 官方 class，且无 Tailwind visual utility 作为主实现

### Requirement: 统一空状态

系统 SHALL 提供以 Tabler 官方 `empty`/`empty-img`/`empty-title`/`empty-subtitle`/`btn` 结构为基础的统一 `EmptyState` 组件，支持标题、描述、主操作、次操作与建议列表，并用于所有页面空态。

#### Scenario: 时间线无记录
- **WHEN** 时间线没有任何 Entry
- **THEN** 显示 Tabler empty composition 并给出记录入口

#### Scenario: 搜索无结果
- **WHEN** 搜索返回 0 条结果
- **THEN** 显示 Tabler empty composition 与可操作建议：缩短关键词、切换语义搜索、放宽来源范围、移除筛选条件

#### Scenario: 搜索未执行
- **WHEN** 用户尚未发起搜索
- **THEN** 页面以 Tabler list/card/grid composition 呈现二级内容模块，而不是大片空白

### Requirement: 统一 AI 状态

Entry 的一级视图 SHALL 只显示单一总状态，取值限定为 处理中 / 已整理 / 需复核 / 失败，并使用 Tabler `status`/`badge` semantic class；逐项详情使用 Tabler offcanvas/modal/list composition。

#### Scenario: 状态映射
- **WHEN** Entry 的 AI 处理状态为 pending 或 retrying
- **THEN** 一级视图显示 Tabler processing 状态「处理中」

#### Scenario: 需复核
- **WHEN** Entry 为部分处理完成
- **THEN** 一级视图显示 Tabler warning/review 状态「需复核」

#### Scenario: 状态详情
- **WHEN** 用户点击 AI 状态
- **THEN** 打开 Tabler offcanvas/modal 展示逐项处理明细与失败项重试入口

### Requirement: 记录页以捕获为核心

记录页 SHALL 以 Tabler `card`、`form-control`、`input-group`、`btn`、`dropdown` 和官方 file/dropzone pattern 组成 Capture Workspace，下方仅展示最近记录，不得呈现完整时间线浏览能力。

#### Scenario: 记录页结构
- **WHEN** 用户打开记录页
- **THEN** 页面依次呈现 Tabler page-header、capture card、最近记录 list/card-list 与「查看全部」入口

#### Scenario: 最近记录数量受限
- **WHEN** 记录页加载列表
- **THEN** 仅展示最近 8 条以内记录，且不显示时间范围与类型筛选器

#### Scenario: 查看全部
- **WHEN** 用户点击「查看全部」
- **THEN** 跳转到时间线页

### Requirement: 时间线页为完整历史浏览器

时间线页 SHALL 提供基于 Tabler `activity`/`timeline`/`list-group`/`table` 的完整筛选、日期分组与分页能力。

#### Scenario: 日期分组
- **WHEN** 时间线渲染 Entry
- **THEN** 按日期分组，分组标题使用 Tabler divider/typography 结构而非自定义饱和色胶囊

#### Scenario: 完整分页
- **WHEN** 用户滚动到列表底部
- **THEN** 可继续加载更早的记录，并使用 Tabler pagination/loading pattern 提供反馈

### Requirement: Entry 一级信息收敛

`EntryListItem` SHALL 在 Tabler `list-group`/`card-list`/`activity` 结构中展示时间、类型、2–4 个标签、正文或摘要、AI 总状态、收藏与更多操作；SHALL NOT 默认展示 Embedding、分类、实体、关系、Prompt 版本、Worker 与 Job 明细。

#### Scenario: 默认视图
- **WHEN** Entry 出现在记录页或时间线页
- **THEN** 不直接显示逐项 AI 处理状态或 Job 标识

#### Scenario: 更多操作
- **WHEN** 用户打开 Entry 的 Tabler dropdown 更多菜单
- **THEN** 菜单包含复制、固定、编辑、查看历史、重新 AI 处理、删除

#### Scenario: 查看历史
- **WHEN** 用户选择「查看历史」
- **THEN** 展示 Tabler list/timeline/detail 结构的版本列表与差异（只读）

### Requirement: 搜索工作区

搜索页 SHALL 在未搜索、有结果、无结果三种状态下均呈现基于 Tabler `search-results`、`input-group`、`card`、`list-group`、`table` 和 `empty` 的完整页面内容。

#### Scenario: 未搜索态内容
- **WHEN** 用户尚未搜索
- **THEN** 至少展示「保存的搜索」与「知识对象」两个 Tabler list/card 模块，数据来自已有接口

#### Scenario: 有结果态
- **WHEN** 搜索返回结果
- **THEN** 显示结果计数与每条结果的片段、时间、来源、标签与命中类型徽标

#### Scenario: 命中类型
- **WHEN** 结果由不同检索方式命中
- **THEN** 以 Tabler badge/status variant 区分精确匹配、语义匹配、实体匹配、记忆匹配

#### Scenario: 结果与时间线区分
- **WHEN** 渲染搜索结果
- **THEN** 使用 Tabler search-results/list composition，而非时间线 Entry 布局

### Requirement: 问记忆工作区

问记忆页 SHALL 在未提问与已回答两种状态下均呈现基于 Tabler `chat`、`chat-bubbles`、`chat-bubble`、`card`、`list-group` 和 `offcanvas` 的完整工作区，Sources SHALL 作为一级界面元素。

#### Scenario: 未提问态
- **WHEN** 用户尚未提问
- **THEN** 展示示例问题与最近提问，并使用 Tabler list/card composition

#### Scenario: 回答态桌面布局
- **WHEN** 用户提问并得到回答
- **THEN** 展示 Tabler chat 对话列与 Sources 栏，Sources 显示来源标题、时间、类型与命中片段

#### Scenario: Sources 跳转
- **WHEN** 用户点击某条来源
- **THEN** 可打开对应原始 Entry 或证据链接

#### Scenario: 移动端来源
- **WHEN** 用户在移动端查看回答
- **THEN** 通过 Tabler offcanvas/button pattern 打开来源面板，而非保留双栏

#### Scenario: 追问
- **WHEN** 用户在答案下方继续追问
- **THEN** 发起新的单轮提问（不保留多轮会话上下文）

### Requirement: 无虚假业务模块

页面完整度 SHALL 来自真实信息结构、Tabler empty/list/card/table/detail 状态、结果区与来源区；SHALL NOT 新增无后端支撑的统计、评分或图表模块。

#### Scenario: 最近搜索来源
- **WHEN** 展示「最近搜索」或「最近提问」
- **THEN** 数据来自用户本机真实操作记录，不出现伪造示例数据

#### Scenario: 知识对象
- **WHEN** 展示知识对象模块
- **THEN** 数据来自已有 projects / topics / entities 接口，且文案不宣称「最近使用」

## ADDED Requirements

### Requirement: 全站 Route Tabler 映射

所有用户可访问的主路由、嵌套详情、设置子路由、Prompt/Job/Memory 子页面、认证页、404/error 页及可独立验证的 modal/offcanvas surface SHALL 在 `STARMEM_PAGE_INVENTORY.md` 中逐项列出，归入六类 StarMem 母版，并拥有 Tabler source mapping 与 `completed` 状态才能声明迁移完成。

#### Scenario: 页面清单完整
- **WHEN** 执行 Route audit
- **THEN** 清单覆盖 router、lazy/nested route、auth、error、detail、settings child 和 modal-driven surface，不得因原实现是状态页或 Drawer 而遗漏

#### Scenario: 迁移完成门禁
- **WHEN** 任一页面仍为 `not-reviewed`、`mapped`、`in-progress` 或 `blocked`
- **THEN** 全站迁移不得标记为完成，并必须报告剩余页面与阻塞原因

### Requirement: Tabler 官方页面结构保真

每个迁移页面 SHALL 由 Tabler 官方 page/layout/component 的 DOM hierarchy 和 class 直接 React 化；只允许替换业务文字、数据、路由、图标语义、事件和条件渲染，不得为了审美自行增删 spacing、size、color、radius、shadow、container 或 breakpoint class。

#### Scenario: 结构核对
- **WHEN** 对关键页面执行 class fidelity audit
- **THEN** 能从 `TABLER_SOURCE_MAP.md` 找到 Tabler source file、原始 class、StarMem component 和最终 class，差异均有业务/兼容说明

#### Scenario: 视觉属性修改
- **WHEN** 实现者想增加视觉 utility 或 inline style
- **THEN** 只有在存在对应的 Tabler 官方 composition 或已记录为必要 glue deviation 时才允许，其他情况必须保持官方 class
