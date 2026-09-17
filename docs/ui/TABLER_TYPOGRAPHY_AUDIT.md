# Tabler Typography Audit

审计日期：2026-09-16

## Source / Runtime

~~~
TABLER_REPOSITORY=https://github.com/tabler/tabler.git
TABLER_COMMIT=0776b88863690c9740d7d33988a8b5df66aad6dc
TABLER_VERSION=1.5.1
TABLER_REFERENCE_URL=http://localhost:3000
STARMEM_URL=http://localhost:18780
TABLER_INSTALL_COMMAND=pnpm install --frozen-lockfile
TABLER_BUILD_COMMAND=pnpm run build
TABLER_PREVIEW_COMMAND=pnpm --filter @tabler/preview dev
~~~

官方 Preview 已按仓库 package.json 的 pnpm --filter @tabler/preview dev 启动，并可访问 http://localhost:3000/layout-vertical.html。StarMem 当前 Compose Web 可访问 http://localhost:18780/。

## Tabler 官方实现

事实来源：

- Sans stack：.reference/tabler/core/scss/_variables.scss:383-389
- Root tokens：.reference/tabler/core/scss/bootstrap/_root.scss:58-70
- Body rule：.reference/tabler/core/scss/bootstrap/_reboot.scss:42-55
- Body feature settings：.reference/tabler/core/scss/layout/_core.scss:8-20
- Page title：.reference/tabler/core/scss/layout/_page.scss:108-118
- Component font rules：.reference/tabler/core/scss/bootstrap/_buttons.scss、_forms.scss、_navbar.scss、ui/_badges.scss、ui/_cards.scss

| 项目 | Tabler pinned 实现 |
| --- | --- |
| Default sans stack | system-ui, -apple-system, BlinkMacSystemFont, San Francisco, Segoe UI, Roboto, Helvetica Neue, sans-serif |
| Monospace stack | ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, Courier New, monospace |
| Demo font import | 无；$font-google: null，不加载 Inter/InterVariable Web Font |
| Font resource source | 当前为浏览器/操作系统字体，无远程字体资源 |
| Body font-size | 0.875rem → Chromium 14px |
| Body line-height | 1.4285714286 → Chromium 20px |
| Body font-weight | 400 |
| Body letter-spacing | 0 / Chromium normal |
| Body font-feature-settings | 'liga' 0、'cv03'、'cv04'、'cv11'；Chromium serialization 为 "cv03", "cv04", "cv11", "liga" 0 |
| Body text-rendering | optimizeLegibility |
| .page-title | 20px / 28px / 600 |
| .nav-link | 14px / 20px / 400（active state 依官方状态可为 500） |
| .form-control | 14px / 20px / 400 |
| .btn | 14px / 20px / 500 |
| .badge | 12px / 12px / 500，letter-spacing 0.04em |
| .card-title | 16px / 24px / 500 |
| .table cell | 继承 body：14px / 20px / 400 |
| code / pre | monospace stack，Chromium 12px / 17.1429px |
| .small | 12.25px / 17.5px / 400 |

## StarMem 迁移前实际值

在当前 StarMem /capture 上通过 Chromium 读取：

~~~
document.fonts.check('14px InterVariable') = true
document.fonts.check('14px Inter') = true
getComputedStyle(document.body).fontFamily = system-ui, -apple-system, BlinkMacSystemFont, "San Francisco", "Segoe UI", Roboto, "Helvetica Neue", sans-serif
getComputedStyle(document.body).fontSize = 14px
getComputedStyle(document.body).lineHeight = 20px
getComputedStyle(document.body).fontFeatureSettings = "cv03", "cv04", "cv11", "liga" 0
~~~

document.fonts.check 对未加载字体名也可能返回 true，因此不能作为实际字体证明。CDP CSS.getPlatformFontsForNode 的实际结果为：

| 样本 | Reference（默认 lang=en） | StarMem（lang=zh-CN） |
| --- | --- | --- |
| Latin / Number | Noto Sans | Noto Sans |
| Chinese | Noto Sans CJK JP（Reference 默认英文 locale） | Noto Sans CJK SC |
| Mixed CJK/Latin | Noto Sans CJK JP + Noto Sans | Noto Sans CJK SC + Noto Sans |
| Code / Monospace | Liberation Mono | Liberation Mono |

Reference Preview 默认以 lang=en 启动，已加载后的语言属性变更不会重新 shaping 已存在的中文节点；验证器现在在注入 Fixture 前设置 zh-CN，使两侧以相同文档语言、同一官方字体栈进行比较。Latin、数字、monospace、字号、字重、行高、字距和 feature settings 不得变化。

## StarMem 修复后实际值

在 /__ui/tabler-typography-fixture 上等待 document.fonts.ready 后读取：

~~~
document.fonts.check('14px InterVariable') = true
document.fonts.check('14px Inter') = true
document.fonts.check('14px Noto Sans SC') = true  # 仅辅助检查，不代表实际使用
getComputedStyle(document.body).fontFamily = system-ui, -apple-system, BlinkMacSystemFont, "San Francisco", "Segoe UI", Roboto, "Helvetica Neue", sans-serif
getComputedStyle(document.body).fontSize = 14px
getComputedStyle(document.body).lineHeight = 20px
getComputedStyle(document.body).fontFeatureSettings = "cv03", "cv04", "cv11", "liga" 0
~~~

CDP 真实字体结果与相同 lang=zh-CN 的 Reference Fixture 一致：Latin/数字为 Noto Sans，中文为 Noto Sans CJK SC，Code 为 Liberation Mono；8 个 Fixture 组合均通过 computed style、rendered font、bounding box、overflow、network 和 console gate。

## 本轮修复目标

StarMem 最终 sans token 完全继承 Tabler 官方实现，不追加 CJK fallback：

~~~
system-ui, -apple-system, BlinkMacSystemFont, San Francisco,
Segoe UI, Roboto, Helvetica Neue, sans-serif
~~~

当前没有 Typography 字体偏差；CJK 与 Reference Fixture 在统一 shaping 条件下严格一致。自动化结果由 artifacts/ui/ 和 STARMEM_TABLER_FONT_VERIFICATION_REPORT.md 记录；最终 computed style 与 rendered font 结果均为 PASS。
