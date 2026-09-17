# StarMem UI V2 信息架构审计

> 审计对象：`starmem-v2-ui-preline-refactor` 完成后的前端状态
> 目标 change：`starmem-ui-v2-page-architecture`
> 审计方式：只读代码与接口核对（`web/src/main.tsx`、`web/src/api.ts`、`backend/app/api.py`）

## 一、当前问题

### 1.1 页面骨架同质化

四个主页面共用同一结构：`PageHeader（自造） + 输入/筛选 + 列表或空白`。

| 页面 | 当前结构 | 角色是否清晰 |
|---|---|---|
| 记录（`capture`） | Capture + 完整 Timeline（含筛选） | ✗ 与时间线重复 |
| 时间线（`timeline`） | Timeline（含筛选） | ✗ 与记录页几乎相同 |
| 搜索（`search`） | 搜索框 + 高级过滤 + 结果 | △ 未搜索时接近空白 |
| 问记忆（`ask`） | 输入框 + 答案 + Sources | △ 未提问时接近空白 |

### 1.2 主内容过空

- 搜索页未执行时只有搜索栏与过滤器，主体区域为空。
- 问记忆页未提问时只有输入框。
- 两页均无 second content，缺少「完整页面状态」。

### 1.3 列表信息层级失衡

Entry 卡片默认展开区包含：逐项 AI 处理状态、相关记录、AI 关系、Metadata 表单、标签/实体管理。
这些内容属于「详情与调试」，却与时间、正文处于同一视觉层级。

### 1.4 状态语义分散

| 位置 | 文案 |
|---|---|
| Entry 卡片 | `已索引` / `等待 AI 处理` / `部分处理完成` / `AI 处理失败` |
| Inbox | `新建` / `处理中` / `已处理` / `失败` |
| Job 列表 | 直接展示原始 `status` 值（如 `prompt_validation_failed`） |

同一概念存在多套措辞。

## 二、重复组件

当前以下结构在各页面被重复实现，未抽象：

| 结构 | 出现位置 |
|---|---|
| 页面标题区（标题 + 描述/计数） | 记录、时间线、搜索、问记忆、Inbox、Workbench、设置 |
| 筛选行（select / date / scope） | 时间线、搜索、Workbench |
| 空状态文案 | 时间线、Inbox、搜索、结果区、Workbench |
| 卡片容器 class 字符串 | 各页面各自定义 `cardClass` / `chipClass` 等局部常量 |
| 来源展示 | 问记忆 Sources、搜索结果 |

局部 className 常量在 `main.tsx` 中重复定义 6 次以上（`primaryButtonClass`、`secondaryButtonClass`、`chipClass`）。

## 三、页面角色冲突

1. **记录 vs 时间线**：两者渲染同一 `Timeline` 组件、同一筛选器、同一分页。用户无法区分「快速记录」与「浏览历史」。
2. **搜索 vs 时间线**：搜索结果卡片与时间线卡片结构接近，但语义不同（检索命中 vs 时间对象），当前未区分。
3. **问记忆 vs 搜索**：两者都是「输入 + 结果」，缺少模式差异；Ask 的 Sources 本应是一级 UI，实际是答案的附属栏。

## 四、旧视觉债务

上一 change 已清理自定义 CSS（`styles.css` 325 → 55 行），剩余债务：

- `main.tsx` 中 6 组局部 className 常量重复；
- `details`/`summary` 折叠与 Drawer 混用，缺少统一「二级详情」模式；
- 列表项 `<article>` 结构在各页面独立实现，未抽象为组件。

## 五、可复用业务逻辑（不改动）

| 能力 | 接口 | 现状 |
|---|---|---|
| 保存的搜索 | `GET/POST/PATCH/DELETE /saved-searches` | 已接入 |
| Entry 版本历史 | `GET /entries/{id}/versions`、`/versions/{n}/diff` | **未接入 UI** |
| 逐项 AI 状态 | `GET /entries/{id}/ai-status` | 已接入（位置不当） |
| 知识对象 | `GET /projects`、`/topics`、`/entities` | 已接入 Workbench |
| 时间回顾 | `GET /reviews` | 已接入 Workbench |
| 相似 / 关系 / 标签 / 实体 / 元数据 / 安全 | `GET /entries/{id}/*` | 已接入 Entry 展开区 |
| 附件 | `GET /attachments/{id}` | 已接入 |

## 六、能力缺口（本次不引入后端变更）

| 需求 | 现状 | 处理 |
|---|---|---|
| 「最近搜索」 | 无接口 | localStorage 记录 |
| 「最近提问」 | 无接口 | localStorage 记录 |
| 「常用来源」 | 无接口 | 不实现；改用「知识对象」 |
| 多轮会话 / 追问上下文 | `POST /ask` 单轮无状态 | 保持单轮，追问=新提问 |
| AI 生成追问建议 | 无 | 使用静态可点击示例问题 |

## 七、结论

本次改造属于 **Information Architecture + Layout + Template Fidelity**，不是颜色调整：

1. 抽取 6 个公共组件，消除重复结构；
2. 拆分记录页与时间线页的数据流与信息层级；
3. 为搜索页与问记忆页补齐完整三态；
4. 把 AI 明细从一级视图降到 Drawer，并统一状态语义；
5. 接入已有但未使用的版本历史接口。

视觉体系不变，继续以 Preline 为唯一来源。
