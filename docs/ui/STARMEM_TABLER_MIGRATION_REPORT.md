# StarMem Tabler 严格模板迁移报告

日期：2026-09-16

## 结论

StarMem 已完成全站 Tabler 严格模板迁移：23 个用户可访问 Route/逻辑页面表面全部完成 Inventory、母版归类、官方 Source Mapping、Tabler DOM/class 迁移和状态/响应式验收。视觉源固定为 Tabler 官方仓库及其构建产物，业务 API、数据库、Memory/Search/Prompt/Worker 逻辑未因本次 UI 迁移修改。

## Tabler 来源与构建证据

| 项 | 实际值 |
| --- | --- |
| Repository | `https://github.com/tabler/tabler.git` |
| Commit | `0776b88863690c9740d7d33988a8b5df66aad6dc` |
| Version | `1.5.1`（官方 `core/package.json` / build banner） |
| Clone time | `2026-09-16 17:24:21 +0800` |
| Install | `pnpm install --frozen-lockfile`，通过 |
| Build | `pnpm run build`，通过 |
| Preview | `pnpm --filter @tabler/preview dev`，`http://localhost:3000`，通过 |
| Icons | `@tabler/icons-react@3.46.0` |
| Production CSS | `web/src/vendor/tabler/tabler.css` + 官方 `tabler-vendors.css` / `dropzone.css` |
| Production JS | 官方 `tabler.esm.js` 与 `tabler-theme.esm.js` |

详细构建源、复制清单和 SHA-256：[`TABLER_VENDOR_INFO.md`](TABLER_VENDOR_INFO.md)。官方 DOM/class 映射：[`TABLER_SOURCE_MAP.md`](TABLER_SOURCE_MAP.md)。

## Route Inventory

- Route/逻辑页面总数：23。
- 覆盖：登录、Capture、Timeline、Search、Ask、Ask Sources、Inbox、Workbench 及对象详情、Sources、Settings 子页、Prompt 版本/测试、AI Jobs 及详情、Memory 及详情、Entry 详情/历史、404/Error。
- 六类母版：Capture、Browse、Search、AI、Detail、Management；每个页面只归入一种。
- 全部清单状态已更新为 `completed`：[`STARMEM_PAGE_INVENTORY.md`](STARMEM_PAGE_INVENTORY.md)。
- 全站问题审计：[`STARMEM_FULL_SITE_UI_AUDIT.md`](STARMEM_FULL_SITE_UI_AUDIT.md)。

## Before / After

| 区域 | Before | After |
| --- | --- | --- |
| Shell | Preline/Tailwind 混合壳层、页面间布局不同 | 官方 `.page` + `.navbar.navbar-vertical` + `.page-wrapper` + `.page-header` + `.page-body` + `.container-xl` |
| Capture | 自行拼装 Composer 与文件区域 | Tabler `card/form-control/btn/dropdown`，文件模式使用官方 `.dropzone/.dz-message` |
| Browse | 自定义 Feed/Row | 官方 `activity/list-group/table/row/col` 组合，保留真实过滤和分页 |
| Search | 自定义搜索框/结果卡 | 官方 `form-control/form-select/list-group/empty/badge` 组合，覆盖未查询、结果、无结果 |
| Ask | 单一输入框 | 官方 Chat/Chat Bubble 组合，Sources 为桌面一级栏、移动 Offcanvas |
| Detail | 大 Card + 字段列表或 Drawer | 官方 Card/Datagrid/List/Timeline/Markdown 组合，主内容 + 元数据 Rail |
| Management | 设置、Prompt、Jobs 共用简单单列 | 官方 Settings/Form/Tabs/Table/Datagrid/Status/Alert 组合，保留真实动作与状态 |
| Auth/Error | 自定义单列页 | 官方 Auth/Empty/Error Composition，仅替换 StarMem 文案和事件 |

## 官方参考截图与 StarMem 截图

官方参考截图位于 [`docs/ui/reference/tabler/`](reference/tabler/)，StarMem 最终截图位于 [`docs/ui/screenshots/tabler/`](screenshots/tabler/)。以下为关键一一对应：

| Tabler 官方参考 | StarMem 最终页面 |
| --- | --- |
| [`layout-vertical.png`](reference/tabler/layout-vertical.png) | [`desktop-record.png`](screenshots/tabler/desktop-record.png) |
| [`dropzone.png`](reference/tabler/dropzone.png) | [`desktop-record-file.png`](screenshots/tabler/desktop-record-file.png) |
| [`activity.png`](reference/tabler/activity.png) | [`desktop-timeline.png`](screenshots/tabler/desktop-timeline.png) |
| [`search-results.png`](reference/tabler/search-results.png) | [`desktop-search-results.png`](screenshots/tabler/desktop-search-results.png) / [`desktop-search-no-results.png`](screenshots/tabler/desktop-search-no-results.png) |
| [`chat.png`](reference/tabler/chat.png) | [`desktop-ask-empty.png`](screenshots/tabler/desktop-ask-empty.png) / [`desktop-ask-answer.png`](screenshots/tabler/desktop-ask-answer.png) |
| [`settings.png`](reference/tabler/settings.png) | [`desktop-settings.png`](screenshots/tabler/desktop-settings.png) / [`desktop-model-settings.png`](screenshots/tabler/desktop-model-settings.png) |
| [`tables.png`](reference/tabler/tables.png) | [`desktop-ai-jobs.png`](screenshots/tabler/desktop-ai-jobs.png) / [`desktop-prompt-version.png`](screenshots/tabler/desktop-prompt-version.png) |
| [`auth.png`](reference/tabler/auth.png) | [`desktop-login.png`](screenshots/tabler/desktop-login.png) |
| [`error-page.png`](reference/tabler/error-page.png) | [`desktop-404.png`](screenshots/tabler/desktop-404.png) |

最终截图还覆盖 Entry/Memory/Entity/Workbench/Source/Inbox/Prompt Tests、Entry History、AI Job Detail，以及 `390×844` 和 `430×932` 的 Record、Timeline、Search、Ask、Settings、Prompt Studio，并额外保存 `1920×1080` Record 截图。截图生成数量：37 张。

## 代码与资产变更

- `web/src/vendor/tabler/` 使用 pinned Tabler 官方 CSS/JS/theme、官方 vendor CSS 和 Dropzone CSS；所有 vendor 文件与 `.reference/tabler` 对应文件逐一 `cmp` 一致，未修改上游 selector。
- `web/src/styles.css` 只保留官方 CSS import、iOS safe-area、浏览器横向溢出保护和 reduced-motion 功能 glue。
- `web/src/components/AppShell.tsx`、`web/src/components/ui.tsx`、`web/src/theme/tabler.ts` 和 `web/src/components/icons.tsx` 统一输出官方 Tabler/Bootstrap DOM、data API 和 Tabler Icons。
- Record、Timeline、Search、Ask、Inbox、Workbench、Sources、Entry/Memory/Job/Workbench Detail、Settings、Models、Prompt、Jobs、Backup、Login、404 全部接入统一 Shell 和共享状态组件。
- 原图 [`assets/starmenlogo.png`](../../assets/starmenlogo.png) 保留在项目中；运行时使用 [`web/public/starmem-logo.png`](../../web/public/starmem-logo.png)，透明边界已裁剪为 `1129×984`，通过官方 `.navbar-brand-image` 尺寸使用。
- 后端 API、数据库 schema、Worker、检索与记忆逻辑未作 UI 迁移以外的修改。

## 清理与审计

- `preline`、`hs-*`、`lucide-react`、Tailwind Vite/CSS 入口已从生产前端移除；旧 `PRELINE_SOURCE_MAP.md` 已明确标记为历史文档，不能作为新页面依据。
- `web/src` 无新增 arbitrary Tailwind value、hard-coded color、视觉 inline style、私有字体/字号/圆角/阴影和旧 custom-card/custom-panel 视觉 selector。
- CSS 非 vendor 文件仅有 `web/src/styles.css`；新增规则仅为 safe-area、overflow 和 reduced-motion，偏差已记录在 [`TABLER_DEVIATIONS.md`](TABLER_DEVIATIONS.md)。
- Status 使用 Tabler `status`/`badge` semantic class；普通 Tag 与系统状态分层，不再使用业务自定义颜色。
- 运行期文件选择保留真实 API 提交流程，但视觉和 DOM 使用官方 Dropzone Composition；此 React integration 已在偏差表说明。

## 验证结果

| 验证 | 实际结果 |
| --- | --- |
| `curl http://localhost:18000/health` | `database=true`、`redis=true` |
| `docker compose exec -T api pytest -q` | `50 passed, 8 warnings` |
| `docker compose exec -T api ruff check app tests alembic` | `All checks passed!` |
| `docker compose exec -T api ruff format --check app tests alembic` | 既有失败：`backend/app/providers.py:323`，本次 UI 未修改该文件 |
| `npm run lint` | TypeScript 通过 |
| `npm run build` | TypeScript/Vite 通过 |
| `docker compose build web` | 通过 |
| `scripts/smoke.sh` | `integration-smoke: passed` |
| `tests/playwright_smoke.py` | `playwright-smoke: passed` |
| `tests/playwright_traversal.py` | `playwright-traversal: passed`（长序列仅用临时 1000 req/min QA override，已删除并恢复默认 120） |
| `tests/playwright_composition.py` | `passed (25 routes; 6 viewports; dark mode)` |
| Browser console/page errors | Composition QA 与最终截图链路无新增错误 |
| Horizontal overflow | Composition QA 在 `390/430/768/1024/1440/1920` 检查通过 |
| Vendor integrity | pinned 官方文件逐一 `cmp` 一致，checksum 与 vendor info 一致 |

测试覆盖真实登录、Capture 文本/URL/文件、Dropzone 入口、Timeline filter、Search 三态、Ask/Source、Entry/History、Workbench、Inbox 修正/重试、Memory 生命周期、Prompt clone/draft/tests、Jobs、Backup、PWA manifest/Share Target、移动导航、暗色主题和详情返回/关闭。

## 偏差、限制与剩余事项

- StarMem 是 React 单页入口，不能逐页复制 Astro 文件路由；页面 hierarchy/class family 保持官方，路由和 API 事件由 React 绑定。
- Prompt Studio、Memory、Sources 等业务页在 Tabler 中没有同名成品页，使用官方 Settings/Form/Table/Chat/List/Datagrid/Offcanvas Composition，未创造新视觉 primitive。
- Dropzone 使用官方 CSS/DOM，但没有启用其默认自动上传插件，因为 StarMem 必须先走既有 Inbox/API 队列；文件选择、拖放、选中文件、大小、错误和提交仍由现有 React/API 闭环处理。
- 本轮未在真实 iOS Safari 硬件上安装 PWA；浏览器矩阵已验证 safe-area glue、移动 Shell、Drawer、长文本和横向溢出。真机验收仍是环境相关事项。
- 长序列 Playwright 验收需要临时提高限流；产品配置已恢复默认 `120 req/min`，没有把 QA override 写入项目配置。
- 最终截图使用当前本地数据库的真实记录，其中可能包含此前验收生成的测试记录；没有在前端添加假 KPI、假图表、假 Source 或假同步状态。未擅自删除用户数据库数据。
- Vite 对包含官方 Tabler 与图标依赖的单 bundle 给出大于 500 kB 的提示，但构建成功且不影响运行；按需代码分包可作为独立性能任务，不属于本次视觉迁移范围。

## 完成状态

OpenSpec change：[`openspec/changes/starmem-tabler-migration/`](../../openspec/changes/starmem-tabler-migration/)。实现、截图、审计、Inventory 和验证已闭环；未执行 commit、push 或其他远程 Git 操作。
