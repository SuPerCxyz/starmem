## Context

See `proposal.md`. The current pinned Tabler build uses a system sans stack rather than Inter and does not request a web font. StarMem already loads the unmodified Tabler CSS/JS, but its Chinese fallback is implicit and no automated typography evidence exists.

## Goals / Non-Goals

**Goals:**

- Preserve Tabler's official system sans/monospace stacks and all existing typography tokens.
- Add only an explicit, documented CJK fallback after the official Latin stack.
- Provide a deterministic, hidden Fixture and machine-verifiable style/font/bounding-box/screenshot evidence.
- Run the same fixture under the local official Preview and StarMem with identical locale, viewport, DPR, theme, reduced-motion and font-ready gates.
- Audit real StarMem pages after the fixture passes.

**Non-Goals:**

- No layout, composition, Sidebar, card, button, badge, color, radius, shadow, icon, business API, database or worker changes.
- No Inter/InterVariable download or font-face invention because the pinned Tabler source does not use one.
- No screenshot mask, hidden content, relaxed thresholds or visual redesign.

## Decisions

### Use the pinned system stack, then explicit CJK fallback

Use the exact Tabler stack from `core/scss/_variables.scss` as the prefix and append `"Noto Sans SC"`, `"Microsoft YaHei UI"`, `"Microsoft YaHei"`, `sans-serif`. This keeps Latin/number behavior unchanged while making CJK selection deterministic where those fonts exist. Adding a downloaded font was rejected because it would diverge from the official build and create a network dependency.

### Use an internal route with official classes only

Add `/__ui/tabler-typography-fixture` as a direct, non-navigated test route. Its markup is a small official Tabler page composition using IDs only for test targeting and official classes for all appearance. The Reference side receives the same fixture markup at runtime, so no fixture CSS or production visual class is introduced.

### Use Node Playwright plus pixelmatch/pngjs

The required deliverable is `.mjs`, so add the smallest dev-only Node dependencies needed for Chromium automation and PNG comparison. `pixelmatch` with `pngjs` is preferred over an image service; Playwright's Chromium CDP session supplies `CSS.getPlatformFontsForNode`.

### Treat computed style and rendered fonts as hard gates

Collect the nine requested CSS properties plus geometry, text samples and network/console evidence. Compare font-family as an exact official prefix plus the documented CJK suffix; compare all other typography properties exactly after normalizing browser serialization. Bounding boxes use only a 0.5 CSS-pixel rounding tolerance. Pixelmatch compares the Fixture element itself, uses its documented default antialias threshold and a fixed 0.1% maximum diff ratio; this keeps unrelated browser/preview chrome out of the comparison and is not used to hide layout or non-CJK typography drift.

### Start only missing local services

The scripts require `TABLER_REFERENCE_URL` and `STARMEM_URL`. If a URL is unavailable, they use the repository-defined Tabler Preview command and the project Compose command, wait for readiness, and only terminate child processes they directly spawned. Existing services are never stopped by validation.

### Keep generated evidence outside source

All screenshots, JSON evidence and diff images go under `artifacts/ui/`. The audit docs record URLs, commands, font results, pass/fail counts and limitations. No generated artifact is imported by production code.

## Risks / Trade-offs

- [System fonts vary by host] → record platform fonts via CDP; require the same validation host/Chromium for screenshot evidence and allow only the explicit CJK fallback.
- [Reference page and StarMem app use different business data] → compare an identical runtime-injected Fixture for typography, then separately audit real pages.
- [Node browser dependency may not be installed] → use the installed Chromium executable when available and fail with an actionable message if Playwright cannot launch; do not silently skip CDP checks.
- [Long matrix can hit StarMem API rate limits] → the fixture itself is API-free; real pages use the existing login/session and the validator documents the configured QA command without changing product limits.

## Migration Plan

1. Record official and current runtime typography values in `TABLER_TYPOGRAPHY_AUDIT.md`.
2. Add the documented CJK fallback and hidden Fixture route.
3. Install dev-only validation dependencies and implement the two audit scripts plus unified npm commands.
4. Run the validator against the already-built official Preview and StarMem, inspect any diff, and iterate until all hard gates pass.
5. Run existing Web/API regressions, finalize report and leave service configuration unchanged.

Rollback is limited to removing the Fixture/scripts/dependencies and reverting the CJK variable override; no data or API migration is involved.
