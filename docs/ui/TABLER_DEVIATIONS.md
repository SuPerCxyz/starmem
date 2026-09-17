# StarMem Tabler 迁移偏差清单

默认不允许新增视觉 CSS 或改写 Tabler vendor。以下是当前唯一记录的集成偏差：

| 偏差 | 原因 | 规则/影响 |
| --- | --- | --- |
| StarMem Logo 使用 `starmem-logo.png` | 业务品牌必须保留，Tabler Demo 使用自己的 logo | 只放入官方 `.navbar-brand` / `navbar-brand-image` 尺寸，不改变 navbar 高度；原图保留在 `assets/starmenlogo.png` |
| React 事件与 Tabler data API 共存 | Tabler dropdown/offcanvas/collapse 通过 DOM data attributes 工作，业务保存/请求由 React 管理 | 仅使用 React glue 初始化/销毁，不复制 Tabler 视觉规则或重写 vendor JS |
| iOS safe area | PWA Home Indicator / Dynamic Island 需要运行时 inset | 仅保留 `env(safe-area-inset-*)` 功能规则，不承担视觉设计 |
| Raw Markdown / code / JSON overflow | 业务原文长度和代码行宽不可预测 | 仅使用 Tabler 的 `overflow-auto` / `text-break` 等官方 utility，避免改变页面尺寸体系 |
| Dropzone 业务提交流程 | Tabler 官方 Dropzone 默认由插件自动上传，而 StarMem 必须先写入既有 Inbox/API 队列 | 复用官方 `.dropzone` / `.dz-message` DOM、`tabler-vendors.css` 与 `dropzone.css`；文件选择、拖放、列表和提交仍由 React 绑定既有 API，不引入第二套视觉规则 |
| Sources / Prompt Studio / Memory 等无同名 Tabler 成品页 | Tabler 官方提供的是 chat、list、table、datagrid、settings 等通用 page/component | 只允许将真实业务数据放入这些官方 DOM/class；不得新增自定义 Card/Badge/Drawer 视觉 |
| StarMem 单页入口 | 当前应用使用 React history adapter，而非多页面 Astro | `.page`/`page-wrapper`/`page-header`/`page-body`/`container-xl` hierarchy 保持官方，路由和事件由 React 绑定 |

如果新增偏差，必须先在此表中说明官方 class 无法覆盖的原因、规则和影响范围。
