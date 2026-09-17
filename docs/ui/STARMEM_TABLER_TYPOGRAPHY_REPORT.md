# StarMem Tabler Typography 一致性报告

日期：2026-09-16

## 结论

本报告记录前一阶段字体校验；后续已按用户要求移除自定义 CJK fallback，当前字体状态以 STARMEM_TABLER_FONT_VERIFICATION_REPORT.md 为准。

## 来源与运行目标

| 项 | 实际值 |
| --- | --- |
| Tabler commit | 0776b88863690c9740d7d33988a8b5df66aad6dc |
| Tabler version | 1.5.1 |
| Reference URL | http://localhost:3000 |
| StarMem URL | http://localhost:18780 |
| Reference command | pnpm --filter @tabler/preview dev |
| StarMem command | docker compose up -d |
| Fixture route | /__ui/tabler-typography-fixture |
| Browser | Chromium，Playwright，DPR 1 |
| Locale | zh-CN |
| Theme | light / dark |

官方实现与首次运行时值见 TABLER_TYPOGRAPHY_AUDIT.md。

## 官方与 StarMem 字体栈

| 项 | Tabler 官方 | StarMem 最终 |
| --- | --- | --- |
| Sans | system-ui, -apple-system, BlinkMacSystemFont, San Francisco, Segoe UI, Roboto, Helvetica Neue, sans-serif | 官方 stack + Noto Sans SC + Microsoft YaHei UI + Microsoft YaHei + sans-serif |
| Monospace | ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, Courier New, monospace | 完全一致 |
| Body | 14px / 400 / 20px | 完全一致 |
| Feature settings | cv03、cv04、cv11、liga 0 | 完全一致 |
| Text rendering | optimizeLegibility | 完全一致 |
| Web font | 无 | 无 |

Tabler pinned 源码的 font-google 为 null，因此没有引入 Inter 或 InterVariable。StarMem 只在官方 sans stack 的系统字体顺序中加入明确 CJK fallback；字号、字重、行高、字距、feature settings 和 monospace 未改动。偏差已记录在 TABLER_DEVIATIONS.md。

## document.fonts.check

最终 Fixture 在 document.fonts.ready 之后的结果：

~~~
document.fonts.check('14px InterVariable') = true
document.fonts.check('14px Inter') = true
document.fonts.check('14px Noto Sans SC') = true
~~~

Inter/InterVariable 的 check 结果不能证明浏览器实际使用了该字体，因为浏览器对未加载字体名也可能返回 true；实际字体以 CDP platform fonts 为准。

## Rendered Fonts

通过 Chromium CDP CSS.getPlatformFontsForNode 采集，8 个 Fixture 组合全部通过：

| 样本 | Reference | StarMem | 判定 |
| --- | --- | --- | --- |
| Latin | Noto Sans | Noto Sans | PASS |
| Number | Noto Sans | Noto Sans | PASS |
| Chinese | Noto Sans CJK JP | Noto Sans CJK SC | PASS，记录中的 CJK fallback |
| Mixed CJK/Latin | Noto Sans + Noto Sans CJK JP | Noto Sans + Noto Sans CJK SC | PASS，记录中的 CJK fallback |
| Monospace | Liberation Mono | Liberation Mono | PASS |

完整原始结果：artifacts/ui/tabler-rendered-fonts.json。

## Computed Style Diff

比较属性：

~~~
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

Fixture 在每个 viewport/theme 的 style differences 均为 0。font-family 只允许官方 stack 后的记录 CJK fallback，其余属性严格一致。

| Fixture / Theme | Computed Style | Rendered Font | Bounding Box | Overflow |
| --- | --- | --- | --- | --- |
| 1440x1000 light | PASS | PASS | PASS | 0 |
| 1440x1000 dark | PASS | PASS | PASS | 0 |
| 1920x1080 light | PASS | PASS | PASS | 0 |
| 1920x1080 dark | PASS | PASS | PASS | 0 |
| 390x844 light | PASS | PASS | PASS | 0 |
| 390x844 dark | PASS | PASS | PASS | 0 |
| 430x932 light | PASS | PASS | PASS | 0 |
| 430x932 dark | PASS | PASS | PASS | 0 |

## Screenshot Visual Diff

截图使用相同 viewport、DPR、locale、color scheme、reduced motion 和 document.fonts.ready，比较的是 Fixture 元素本身而非外部 Preview chrome。Reference Fixture 准备阶段只移除复制内容之外的 Astro Preview 工具栏，不隐藏或 mask Fixture 内的任何目标节点。pixelmatch 使用固定 threshold 0.1，最大允许差异比例固定为 0.1%，没有动态放宽阈值。

| Fixture / Theme | Screenshot Diff |
| --- | ---: |
| 1440x1000 light | 0.0010% |
| 1440x1000 dark | 0.0010% |
| 1920x1080 light | 0.0007% |
| 1920x1080 dark | 0.0007% |
| 390x844 light | 0.0025% |
| 390x844 dark | 0.0027% |
| 430x932 light | 0.0025% |
| 430x932 dark | 0.0025% |

最终截图目录：

- Reference：artifacts/ui/reference/
- StarMem：artifacts/ui/starmem/
- Diff：artifacts/ui/diff/
- Style JSON：artifacts/ui/tabler-typography-style-diff.json

## Font Network / Console

- Fixture font requests：Reference 0，StarMem 0。Tabler 使用系统字体，没有远程字体资源。
- Font response failures：0。
- console.error：0。
- pageerror：0。
- OTS parsing、decode、CORS font error：0。

## Real Page Typography Audit

脚本自动打开以下真实页面，并按 4 个 viewport × 2 个 theme 检查 body、page-title、Sidebar nav、form-control、button、badge、code/pre 和横向溢出：

~~~text
/capture
/timeline
/search
/ask
/settings
~~~

结果：40/40 page combinations PASS；style mismatch 0；browser/network errors 0；horizontal overflow 0。

原始结果：artifacts/ui/page-typography-audit.json。

## 自动化实现

- scripts/ui/validate-tabler-typography.mjs：服务探测/自动启动、Reference/StarMem Fixture、computed style、CDP rendered fonts、bounding boxes、pixelmatch、network、console、overflow。
- scripts/ui/audit-page-typography.mjs：真实页面 Typography Audit。
- scripts/ui/typography-utils.mjs：固定 viewport/theme/locale/DPR、font-ready、浏览器启动、服务生命周期和证据工具。
- web/src/typography-fixture.html：两侧共用的官方 Tabler DOM/class Fixture 源。
- web/src/components/TablerTypographyFixture.tsx：隐藏 React route，不进入正常导航。

统一命令：

~~~bash
TABLER_REFERENCE_URL=http://localhost:3000 \
STARMEM_URL=http://localhost:18780 \
npm run ui:validate-tabler
~~~

服务不可用时脚本使用 Tabler 官方 Preview 命令和 StarMem Compose 命令启动；已有服务不会被停止。长时间真实页面审计如触发产品默认 API 限流，可通过外部 QA Compose override 临时提高限流，但不会写入产品配置。

## 验证记录

| 命令 | 结果 |
| --- | --- |
| npm run ui:validate-tabler | PASS：8 Fixture combinations + 40 page combinations；使用临时 QA 限流 override，随后已删除并恢复产品默认 120 req/min |
| npm run lint | PASS |
| npm run build | PASS |
| docker compose build web | PASS |
| docker compose exec -T api pytest -q | 既有后端回归结果 50 passed |
| docker compose exec -T api ruff check app tests alembic | PASS |
| tests/playwright_smoke.py | PASS |
| tests/playwright_traversal.py | PASS |
| tests/playwright_composition.py | PASS：25 routes × 6 viewport，包含 dark mode |
| curl http://localhost:18000/health | database=true，redis=true |
| API rate limit | 已恢复产品默认 120 req/min |

第一次页面审计失败是测试选择器将官方 Button/Badge/Code 的 button 语义与普通文本 Fixture 比较，产生了错误差异；已按实际 DOM 语义补充官方参考样本后重跑通过，未放宽强约束。

## 剩余偏差

- CJK 使用显式 fallback：Noto Sans SC、Microsoft YaHei UI、Microsoft YaHei；这是 Tabler Latin stack 不包含完整中文 glyph 的唯一 Typography deviation。
- 本地环境未执行真实 iOS Safari 硬件验收；Chromium 已覆盖 390x844、430x932、safe-area glue、font-ready、overflow 和 dark mode。
- Vite 仍有官方 Tabler/Icons bundle 大于 500 kB 的 warning，不影响本次 Typography 校验。
- 未执行 Git commit、push 或远程 Git 操作。
