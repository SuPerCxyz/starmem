## Why

StarMem already has a Tabler typography audit, but its evidence is organized around the earlier fixture and report names. The stricter acceptance contract needs an explicit rendered-font verification surface so a CSS declaration or `document.fonts.check()` result can never be mistaken for the font Chromium actually paints.

## What Changes

- Add a non-navigated `/__ui/tabler-font-fixture` entry point that reuses the production Tabler typography fixture.
- Add a Playwright + Chromium CDP verifier that records platform fonts node by node and compares them with the running Tabler Reference.
- Add deterministic computed-style, rendered-font, bounding-box, screenshot, font-network, console, and real-page audit artifacts under `artifacts/ui/fonts/`.
- Add `ui:verify-fonts`, `ui:audit-fonts`, and `ui:verify-tabler-fonts` package scripts while keeping the existing audit commands compatible.
- Record the pinned Tabler source, cascade/root-cause checks, results, and the absence of a custom CJK fallback in a dedicated verification report.

## Capabilities

### New Capabilities

- `ui-typography-verification`: deterministic browser proof of Tabler rendered fonts and typography fidelity.

### Modified Capabilities

<!-- No existing product/API requirement changes; this is a verification capability. -->

## Impact

- Frontend test-only route and shared fixture integration in `web/src/`.
- Dev-only Playwright/pixel comparison scripts and npm scripts in `scripts/ui/` and `web/package.json`.
- Generated local QA evidence in `artifacts/ui/fonts/`.
- Documentation and OpenSpec artifacts only; no backend, API, database, worker, layout, or vendor CSS changes.
