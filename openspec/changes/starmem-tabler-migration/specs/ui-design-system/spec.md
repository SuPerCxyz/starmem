## MODIFIED Requirements

### Requirement: 视觉来源唯一性

所有 Web 界面结构 SHALL 复用锁定版本的 Tabler 官方源码、官方 Demo 页面或官方组件源码的 DOM 层级与 class，并 SHALL 在 `docs/ui/TABLER_SOURCE_MAP.md` 中记录来源文件、使用区段和业务替换边界。StarMem 不得继续把 Preline 作为视觉来源。

#### Scenario: 页面可溯源
- **WHEN** 迁移完成一个页面或可独立访问的嵌套页面
- **THEN** 该页面在 `TABLER_SOURCE_MAP.md` 中存在对应 Tabler 页面/组件、源码文件、DOM 区段和最终状态记录

#### Scenario: 无对应免费源码
- **WHEN** 目标页面在 Tabler Demo 中不存在同名成品页
- **THEN** 使用真实存在的 Tabler layout/component 组合，并记录使用的官方 DOM/class 和 deviation，不得自行设计视觉 primitive

### Requirement: 禁止自建视觉与任意值

前端代码 SHALL NOT 新增自建视觉 CSS 类、Tailwind arbitrary value、硬编码颜色、视觉 inline style 或第二套组件库。迁移页面 SHALL 以 Tabler/Bootstrap semantic class 为主要视觉实现；Tabler vendor CSS SHALL 视为只读上游资产，不得被修改。

#### Scenario: 代码扫描
- **WHEN** 对 `web/src`、生产 CSS 入口和 vendor 进行扫描
- **THEN** 不存在本次迁移新增的 `#xxxxxx`、`[13px]`、`shadow-[...]`、自建 card/button/input visual selector，且 vendor checksum 与记录一致

#### Scenario: 功能性 CSS 例外
- **WHEN** 需要 iOS safe area、浏览器兼容或业务内容 overflow
- **THEN** 允许保留最小功能性 CSS，并在 `TABLER_DEVIATIONS.md` 记录原因，不得用它承担字体、颜色、圆角、阴影或组件视觉

### Requirement: 图标体系统一

全站图标 SHALL 使用 Tabler 官方 Icons 或其官方构建产物中的 `icon icon-tabler icon-tabler-*` markup；SHALL NOT 混用 Lucide、Heroicons、Material、Font Awesome 或 emoji 充当图标。StarMem Logo 是唯一例外。

#### Scenario: 替换完成
- **WHEN** Tabler 迁移完成
- **THEN** `lucide-react` 与页面上的 Preline icon 依赖已移除，页面图标均来自 Tabler 官方图标集合，Logo 仍使用裁剪后的 StarMem 资产

### Requirement: 暗色模式

界面 SHALL 使用 Tabler 官方 color-mode 机制、主题属性与 semantic classes，并在浅色与深色下保持文本、边框、表单、表格、对话和状态的可读对比；不得保留 Preline `hs_theme` 作为视觉主题机制。

#### Scenario: 切换主题
- **WHEN** 用户在任一页面切换 Tabler light/dark mode
- **THEN** Shell、页面主体、表单、对话、表格、badge、empty/error state 同步切换，且无 Preline 主题残留导致的不可读区域

### Requirement: 业务功能不回退

视觉层重构 SHALL NOT 改变既有业务行为与 API 契约，包括创建 Entry、Timeline 过滤、Markdown/代码渲染、AI 状态、编辑、删除、Pin、收藏、搜索、问记忆、来源引用、Inbox 修正、Workbench、登录与设置。

#### Scenario: 功能对照
- **WHEN** Tabler 页面替换完成
- **THEN** 重写后的端到端测试覆盖上述链路且全部通过，API 请求路径、请求体和成功/失败反馈保持兼容

### Requirement: 移动端独立布局

移动端 SHALL 使用 Tabler 官方 responsive grid、navbar/offcanvas、form、table 和 detail patterns，而不是将桌面布局等比缩小；允许保留 PWA safe-area 功能集成。

#### Scenario: iPhone 视口
- **WHEN** 在 390px 与 430px 视口打开各页面
- **THEN** 无横向溢出，侧栏通过 Tabler offcanvas、表格使用官方 responsive pattern、Sources/元数据/详情按官方可用模式堆叠或抽屉呈现，safe area 不遮挡操作

### Requirement: 分阶段验收

迁移 SHALL 按 Tabler clone/build/reference → Global Shell → Capture/Timeline → Search/Ask → Detail/Management → Auth/Error → Mobile/Dark/Cleanup 的顺序推进，每个阶段 SHALL 通过对应功能回归、官方来源映射和桌面/移动截图检查后方可进入下一阶段。

#### Scenario: 阶段完成
- **WHEN** 某阶段声明完成
- **THEN** 已执行 Tabler 官方 build、StarMem Web/API 构建与相关 Playwright/测试检查，并产出 1440×1000、1920×1080、390×844、430×932 证据或记录真实阻塞

## ADDED Requirements

### Requirement: Tabler 官方构建资产锁定

生产 Web SHALL 加载从 `.reference/tabler` 的锁定 commit 官方构建得到的 Tabler CSS/JS/字体或官方图标资产；资产来源、构建命令、复制清单和 SHA-256 checksum SHALL 写入 `docs/ui/TABLER_VENDOR_INFO.md`。vendor 文件 SHALL 不被 StarMem 修改。

#### Scenario: vendor 可复现
- **WHEN** 维护者按文档重新构建或核对 vendor 资产
- **THEN** 能从记录的 Tabler commit、官方命令和源文件得到相同 checksum，且 StarMem production entry 只引用该 vendor 资产

#### Scenario: upstream 升级
- **WHEN** 未来需要升级 Tabler
- **THEN** 必须显式更新 commit、build evidence、checksum、source map 和迁移报告，不得由依赖更新自动漂移
