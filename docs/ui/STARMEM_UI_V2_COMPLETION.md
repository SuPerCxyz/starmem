# StarMem UI V2 页面架构重构完成报告

> Change：`starmem-ui-v2-page-architecture`
> 前置：`starmem-v2-ui-preline-refactor`（视觉层迁移到 Preline）已完成
> 本次范围：Information Architecture + Layout + Template Fidelity（不含视觉体系变更）

## 一、改前主要问题

1. 四个主页面共用同一骨架（标题 + 输入框 + 列表/空白），角色不可区分。
2. 搜索页与问记忆页在未操作状态下接近整页空白。
3. 记录页与时间线页渲染同一组件、同一筛选器，功能重复。
4. Entry 卡片默认铺开 AI Pipeline 明细（Embedding / 分类 / 标签 / 实体 / Memory / Relation / Job），噪声高。
5. Header、Filter、Empty State、Badge、Action 各页自造，缺少统一语言。
6. 已存在的 `GET /entries/{id}/versions` 能力完全未接入 UI。

## 二、改后页面结构

### 记录（Capture-first）
```
PageHeader 有什么需要记住的？
Capture Composer（＋ 添加内容 / 保存记录）
最近记录（最多 8 条）            查看全部 →
```

### 时间线（完整历史浏览器）
```
PageHeader 时间线
FilterBar  [全部时间][起始][结束][记录筛选]        共 N 条记录
9月16日周三 ─────────────────────────────
  EntryListItem × N
[加载更多]
```

### 搜索（三态工作区）
```
PageHeader 搜索任何记忆
SearchBar [query][模式][来源][搜索]
高级过滤器（details）
├ 未搜索态：最近搜索 / 保存的搜索 / 知识对象
├ 有结果态：共 N 条结果 + 命中类型徽标 + 检索结果卡
└ 空结果态：EmptyState + 建议（缩短关键词 / 语义搜索 / 放宽范围 / 移除筛选）
```

### 问记忆（AI 记忆工作区）
```
PageHeader 问记忆
Composer [问题][来源范围][询问]
├ 未提问态：可以这样问（示例）/ 最近提问 / EmptyState
└ 回答态：┌ 对话列（你问 + 答案 + 置信度 + 继续追问） ┬ Sources 一级栏 ┐
          └ 移动端：查看 N 条来源 → Bottom Sheet
```

## 三、使用的 Preline 来源

| 结构 | 来源 |
|---|---|
| Sidebar / Navbar / off-canvas | Preline layout blocks（上一 change 引入） |
| AI Composer（Capture / Ask） | Preline AI composer pattern |
| Dropdown 菜单（Entry / Capture ＋） | Preline dropdown markup（React state 控制显隐） |
| Drawer（AI 详情 / 查看历史 / Sources） | Preline overlay + 面板结构，遮罩用 `bg-overlay-inverse/50` |
| Empty State | 新增公共组件，样式取自 Preline 卡片与虚线边框 token |
| Badge / Chip | `bg-layer border-line-3` 语义 token 组合 |
| Form 控件 | `ui.input` / `ui.select` 统一封装 |
| Dark Mode | `.dark` 变体（Preline `hs_theme`） |

## 四、统一的公共组件

新增 `web/src/components/ui.tsx`：

- `PageHeader`（id / title / description / actions）
- `FilterBar`（children / count / countLabel）
- `EmptyState`（title / description / actions / suggestions / icon）
- `AIStatus` + `aiStatusKind()`（processing / ready / review / failed）
- `SourceItem`（index / title / meta / snippet / href / onOpenEntry）
- `ui` 常量集（card / chip / 四类按钮 / input / select / menuItem / 版式类）

`EntryCard` 重构为一级 + Drawer 两级结构；`RecentEntries` 与 `Timeline` 分离。

## 五、删除与收敛

- 各页面重复的局部 className 常量由 6 组降至 2 组（剩余在 `InboxCard` / `MorePage`，可继续收敛）。
- 移除全部全大写营销眉标（CAPTURE FIRST / SEARCH FIRST / SETTINGS & OPERATIONS 等）。
- 移除记录页的时间筛选器（改由时间线页承担）。
- Entry 一级视图移除逐项 AI 状态、Job 标识与 Metadata 表单。
- `styles.css` 保持 48 行（上一 change 已完成清理，本次未新增任何自定义 CSS）。

## 六、Mobile 测试

| 视口 | 记录 | 时间线 | 搜索 | 问记忆 | Sources Sheet |
|---|---|---|---|---|---|
| 390×844 | 0 | 0 | 0 | 0 | 可见 |
| 430×932 | 0 | 0 | 0 | 0 | 可见 |

（数字为 `documentElement.scrollWidth - clientWidth`，即横向溢出像素）

修复记录：初测搜索页 390px 溢出 122px，定位为「保存的搜索」行内长名称按钮未收缩；改为 `min-w-0 truncate` 并隐藏移动端副标题后归零。

## 七、Screenshots

| 文件 | 说明 |
|---|---|
| `/tmp/u2-record-1440.png` | 桌面 · 记录 |
| `/tmp/u2-timeline-1440.png` | 桌面 · 时间线 |
| `/tmp/u3-search-empty-1440.png` | 桌面 · 搜索未搜索态 |
| `/tmp/u3-search-results-1440.png` | 桌面 · 搜索结果 |
| `/tmp/u3-search-noresult-1440.png` | 桌面 · 搜索空结果 |
| `/tmp/u4-ask-empty-1440.png` | 桌面 · 问记忆未提问态 |
| `/tmp/u4-ask-answer-1440.png` | 桌面 · 问记忆回答态 |
| `/tmp/u5-record-390.png` | 移动 · 记录 |
| `/tmp/u5-search-390.png` | 移动 · 搜索 |
| `/tmp/u2-timeline-390.png` | 移动 · 时间线 |
| `/tmp/u4-ask-390.png` | 移动 · 问记忆 |

## 八、验证结果（实际执行）

```
npm run build                                  → ✓ built
docker compose exec -T api pytest -q           → 50 passed
docker compose exec -T api ruff check ...      → All checks passed!
scripts/smoke.sh                               → integration-smoke: passed
python3 tests/playwright_smoke.py              → playwright-smoke: passed
扫描（硬编码颜色 / Tailwind 调色板）            → 0 / 0
```

## 九、Known Limitations

1. **无多轮会话**：`POST /ask` 为单轮无状态，追问等同新提问，不保留上下文。
2. **最近搜索 / 最近提问仅本机**：存于 `localStorage`，不跨设备同步、清理浏览器数据后丢失。
3. **无「常用来源」模块**：后端无 sources 列表接口，未以假数据填充。
4. **「知识对象」非「最近使用」**：数据来自全量 `projects` / `entities`，文案已避免宣称「最近」。
5. **iOS Safe Area 未真机验证**：本环境无 iOS 设备/模拟器，仅核查 `safe-area-*` 类与布局结构。
6. **Dark Mode 未逐页截图验证**：样式完全由 Preline `.dark` 变体驱动，未做视觉回归。
7. **测试残留**：`playwright_smoke.py` 会在 Inbox 留下 ingestion 记录（后端无删除端点）。

## 十、下一步建议

1. 若需要真正的对话式追问，应新增后端会话模型与 `ask` 多轮上下文（独立 change）。
2. 将 `InboxCard` / `MorePage` 的剩余局部 class 常量并入 `ui`，彻底消除重复。
3. 补齐 Dark Mode 逐页截图与 iOS 真机 Safe Area 验证。
4. 视需要为「最近搜索 / 最近提问」提供后端存储，实现跨设备一致。
