# StarMem Tabler Font Verification Report

日期：2026-09-16

## 结论

本次验证只处理字体真实性、CSS Typography cascade 和自动视觉证据，没有修改页面布局、Sidebar、Grid、Container、Card、Button、Badge、Color、Radius、Shadow、Page Composition 或业务/API。StarMem 完全继承 pinned Tabler 官方字体栈，不追加自定义 CJK fallback。最终以 Chromium CDP CSS.getPlatformFontsForNode 为强验收标准：Fixture 8/8 组合、18/18 节点样本和真实页面 40/40 组合均通过。

## Source / Runtime

| 项目 | 实际值 |
| --- | --- |
| Tabler repository | https://github.com/tabler/tabler.git |
| Tabler commit | 0776b88863690c9740d7d33988a8b5df66aad6dc |
| Tabler version | 1.5.1 |
| Reference URL | http://localhost:3000 |
| StarMem URL | http://localhost:18780 |
| Tabler build | pnpm run build |
| Tabler preview | pnpm --filter @tabler/preview dev |
| StarMem fixture | /__ui/tabler-font-fixture |
| Browser | Chromium + Playwright，DPR 1 |
| Locale | zh-CN |
| Themes | light / dark |
| Viewports | 1440x1000、1920x1080、390x844、430x932 |

Reference 使用 .reference/tabler 当前 pinned 源码和实际 Preview；StarMem Web 已重新构建并部署到运行中的 Compose 容器。

## Official Typography

来源：

- .reference/tabler/core/scss/_variables.scss:383-389
- .reference/tabler/core/scss/bootstrap/_root.scss:58-70
- .reference/tabler/core/scss/bootstrap/_reboot.scss:42-55
- .reference/tabler/core/scss/layout/_core.scss:8-20
- .reference/tabler/core/scss/layout/_page.scss:108-118

| 项目 | Tabler 官方实现 |
| --- | --- |
| Sans | system-ui, -apple-system, BlinkMacSystemFont, San Francisco, Segoe UI, Roboto, Helvetica Neue, sans-serif |
| Monospace | ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, Courier New, monospace |
| Web font | 无；$font-google: null，无 Inter/InterVariable @font-face |
| Body | 14px / 400 / 20px |
| Letter spacing | 0 / browser normal |
| Feature settings | "cv03", "cv04", "cv11", "liga" 0 |
| Text rendering | optimizeLegibility |
| Page title | 20px / 28px / 600 |
| Button | 14px / 20px / 500 |
| Badge | 12px / 12px / 500 |
| Code | 官方 monospace stack |

## StarMem Final Stack / Cascade

StarMem 最终 sans token（与 Tabler 官方完全一致）：

~~~text
system-ui, -apple-system, BlinkMacSystemFont, "San Francisco", "Segoe UI",
Roboto, "Helvetica Neue", sans-serif
~~~

Monospace 继续完全继承 Tabler 官方 stack。web/src/styles.css 只加载官方 Tabler CSS 和功能性 safe-area/motion 规则，不再设置 --tblr-font-sans-serif；没有 StarMem @font-face、远程字体资源、inline Typography style 或页面级字体 override。生产源码扫描未发现 Preline、hs-*、Tailwind Typography utility、旧视觉类或新增硬编码颜色。

document.fonts.ready 后的 Fixture 状态：

~~~text
document.fonts.status = loaded
document.fonts.check('14px Inter') = true
document.fonts.check('14px InterVariable') = true
document.fonts.check('14px Noto Sans SC') = true
~~~

这些 check() 值仅作辅助，不能证明实际渲染字体；实际字体以以下 CDP 结果为准。

## Rendered Font：逐节点结果

以下表格来自 CSS.getPlatformFontsForNode。Reference 和 StarMem 在同一 Chromium、locale、viewport、theme 下逐节点采集；所有 CJK、Latin、数字、UUID、技术字符串和 monospace 都必须与 Reference 严格一致。

| Node | Text | Reference rendered font | StarMem rendered font | Result |
| --- | --- | --- | --- | --- |
| Latin title | StarMem | Noto Sans | Noto Sans | PASS |
| Latin Search | Search | Noto Sans | Noto Sans | PASS |
| Latin Settings | Settings | Noto Sans | Noto Sans | PASS |
| Latin Import Inbox | Import Inbox | Noto Sans | Noto Sans | PASS |
| Number | 18:41 · 150W · 3903 | Noto Sans | Noto Sans | PASS |
| UUID | traversal-e910a79d-0072-4a2c-baa1-3385b3c78e57 | Noto Sans | Noto Sans | PASS |
| Technical | node-3903 multipath undef | Noto Sans | Noto Sans | PASS |
| Chinese title | 有什么需要记住的？ | Noto Sans CJK SC | Noto Sans CJK SC | PASS |
| Chinese navigation | 时间线 | Noto Sans CJK SC | Noto Sans CJK SC | PASS |
| Chinese body | 有什么需要记住的？ | Noto Sans CJK SC | Noto Sans CJK SC | PASS |
| Chinese button | 已整理 | Noto Sans CJK SC | Noto Sans CJK SC | PASS |
| Chinese input | 设置 | Noto Sans CJK SC | Noto Sans CJK SC | PASS |
| Chinese select | 需复核 | Noto Sans CJK SC | Noto Sans CJK SC | PASS |
| Chinese badge | 需复核 | Noto Sans CJK SC | Noto Sans CJK SC | PASS |
| Chinese status | 已整理 | Noto Sans CJK SC | Noto Sans CJK SC | PASS |
| Mixed | node-3903 multipath 出现 undef | Noto Sans + Noto Sans CJK SC | Noto Sans + Noto Sans CJK SC | PASS |
| Monospace code | service: starmem / openstack volume create | Liberation Mono | Liberation Mono | PASS |
| Monospace pre | service: starmem | Liberation Mono | Liberation Mono | PASS |

Reference 与 StarMem 的 CJK 节点全部稳定为 Noto Sans CJK SC；没有出现组件间随机 fallback，也没有追加 StarMem 私有字体。

## Computed Style / Bounding Box

比较属性：

~~~text
font-family
font-size
font-weight
font-style
line-height
letter-spacing
font-feature-settings
text-transform
text-rendering
~~~

结果：8/8 viewport/theme 组合 Computed Style differences 为 0；重点节点的 width/height differences 为 0，浏览器舍入容差为 0.5 CSS px。font-feature-settings、font-size、font-weight、line-height、letter-spacing 在 Reference 与 StarMem 中一致。

原始结果：

- artifacts/ui/fonts/computed-style-diff.json
- artifacts/ui/fonts/bounding-box-diff.json

## Screenshot Visual Regression

截图在 document.fonts.ready 后采集，使用相同 viewport、DPR、locale、theme 和 reduced motion。pixelmatch 使用固定 threshold 0.1，最大差异比例固定为 0.1%；没有 mask、隐藏目标节点或动态放宽阈值。

| Viewport / Theme | Diff pixels | Diff ratio | Result |
| --- | ---: | ---: | --- |
| 1440x1000 light | 0 | 0% | PASS |
| 1440x1000 dark | 0 | 0% | PASS |
| 1920x1080 light | 0 | 0% | PASS |
| 1920x1080 dark | 0 | 0% | PASS |
| 390x844 light | 0 | 0% | PASS |
| 390x844 dark | 0 | 0% | PASS |
| 430x932 light | 0 | 0% | PASS |
| 430x932 dark | 0 | 0% | PASS |

产物保留在 artifacts/ui/fonts/reference/、artifacts/ui/fonts/starmem/ 和 artifacts/ui/fonts/diff/。Reference Fixture 准备阶段在注入内容前设置相同的 zh-CN shaping 条件，并移除复制内容之外的 Astro Preview 工具栏；Fixture 内的目标内容未被隐藏或 mask。

## Font Network / Browser Console

- Reference font requests：0
- StarMem font requests：0
- Font response failures：0
- Invalid font content types：0
- Font decode / OTS / CORS errors：0
- console.error：0
- pageerror：0
- Fixture horizontal overflow：0

零字体请求符合 pinned Tabler 的系统字体实现；所有请求、响应、requestfailed、console 和 pageerror 均由 Playwright 监听并作为退出门禁。

## Real Page Font Audit

Fixture 通过后自动审计：

~~~text
/capture
/timeline
/search
/ask
/settings
~~~

覆盖 4 个 viewport × light/dark，共 40 个组合；检查 body、page title、description、Sidebar nav、button、form-control、badge/status、code/pre、table 和横向溢出。

结果：40/40 PASS；unexpected font override 0；browser/network error 0；overflow 0。

原始结果：artifacts/ui/fonts/real-page-font-audit.json。

## 自动化入口

~~~text
scripts/ui/verify-tabler-rendered-fonts.mjs
scripts/ui/audit-page-typography.mjs
scripts/ui/typography-utils.mjs
~~~

新增 npm scripts：

~~~bash
npm run ui:verify-fonts
npm run ui:audit-fonts
npm run ui:verify-tabler-fonts
~~~

ui:verify-tabler-fonts 顺序执行 Reference/StarMem 可用性、font-ready、font network、Rendered Fonts、Computed Style、Bounding Box、Screenshot Diff 和真实页面审计；任意硬门禁失败返回非零，全部通过返回 0。兼容命令 npm run ui:validate-tabler 仍保留并已通过。

## Root Cause / Iteration

这次审计没有发现 StarMem 错误加载 Inter 或字体资源 404；pinned Tabler 本身没有 Web font，实际 Latin 为宿主 Chromium 的 Noto Sans，CJK 与 monospace 分别为 Noto Sans CJK SC 和 Liberation Mono。Reference 默认 lang=en 时，已存在的中文节点会被宿主 shaping 为 JP；验证器已在注入 Fixture 前统一为 zh-CN，使官方 CSS 在两侧产生相同 CJK Rendered Font。

新审计首次运行时发现的失败是测试映射错误：真实页面的第一个 .status 是 button.status，而 Reference 期望节点是 span.status，造成 font-feature-settings/text-rendering 的假差异。补充完全相同的官方 button.status Reference 节点后，严格命令重跑通过；没有放宽规则或修改生产布局。

## Files Changed

- web/src/main.tsx：增加非导航测试入口 alias。
- web/src/typography-fixture.html：增加固定 Latin、UUID、技术字符串和 CJK 控件样本；全部使用生产 Tabler CSS/class。
- web/src/styles.css：移除自定义 CJK fallback，恢复官方 Tabler 字体栈；保留既有功能性规则。
- web/package.json：增加新验证命令。
- scripts/ui/verify-tabler-rendered-fonts.mjs：逐节点 CDP、style、geometry、截图和 runtime gates。
- scripts/ui/typography-utils.mjs：共享 fixture route、font response content-type 和 browser helpers。
- scripts/ui/audit-page-typography.mjs：扩展真实页面节点审计并输出新路径。
- docs/ui/TABLER_DEVIATIONS.md：确认没有自定义 Typography deviation。
- openspec/changes/starmem-tabler-font-verification/：proposal/spec/design/tasks。

Tabler vendor CSS 未修改；应用代码没有新增 !important、视觉 inline style、test-only font override 或 hardcoded color。

## Verification Record

| Command | Result |
| --- | --- |
| npm run ui:verify-tabler-fonts | PASS：8 Fixture combinations + 40 real-page combinations |
| npm run ui:validate-tabler | PASS：兼容校验 8 + 40 |
| npm run lint | PASS |
| npm run build | PASS |
| docker compose build web | PASS，Web 已实际替换运行容器 |
| docker compose exec -T api pytest -q | PASS：50 passed（重跑） |
| docker compose exec -T api ruff check app tests alembic | PASS |
| scripts/smoke.sh | PASS |
| tests/playwright_smoke.py | PASS |
| tests/playwright_traversal.py | PASS |
| tests/playwright_composition.py | PASS：25 routes × 6 viewport，dark mode |
| openspec validate --all --strict | PASS：33 passed，0 failed |

长序列真实页面审计使用临时外部 Compose QA override 提高限流，验证完成后已删除；当前 API STARMEM_RATE_LIMIT_PER_MINUTE=120，健康检查 database/redis 均为 true。验证未执行 Git commit、push 或远程部署。

API 全套测试首次运行受共享本地数据库中既有 V100/power_limit 状态影响，出现 1 个固定数据断言失败；未修改后端代码，单测重跑及随后全量重跑均为 50 passed。该环境状态问题与本次字体验证无关。

## Remaining Deviations / Limitations

- 没有自定义 Typography deviation；StarMem 完全使用 Tabler 官方 sans/monospace stack。不同浏览器/操作系统仍可能选择不同系统字体，这是官方 system stack 的固有行为，不由 StarMem 私自指定。
- 本地未执行真实 iOS Safari 硬件验收；Chromium 已覆盖 390x844、430x932、safe-area glue、font-ready、dark mode 和 overflow。
- ruff format --check 仍存在迁移前既有的 backend/app/providers.py:323 格式问题，本次未触碰该文件。
- Vite 报告官方 Tabler/Icons bundle 大于 500 kB 的既有 warning，不影响字体验证。
