## 1. Typography baseline and source evidence

- [x] 1.1 Re-read pinned Tabler typography source, capture commit/URL/build command, and record official stacks/tokens in `docs/ui/TABLER_TYPOGRAPHY_AUDIT.md`.
- [x] 1.2 Capture current StarMem `document.fonts.check`, computed styles, CDP platform fonts, font requests and console baseline without changing code.

## 2. Tabler typography implementation

- [x] 2.1 Add only the documented CJK fallback after the pinned Tabler sans stack; preserve monospace and all official typography tokens.
- [x] 2.2 Add the hidden `/__ui/tabler-typography-fixture` route with deterministic official Tabler DOM/classes and fixed samples, without adding it to navigation.
- [x] 2.3 Add the CJK fallback reason and unchanged typography properties to `docs/ui/TABLER_DEVIATIONS.md`.

## 3. Automated fidelity tooling

- [x] 3.1 Add the minimal dev-only Node Playwright/PNG comparison dependencies and package scripts for the two audits plus the unified validator.
- [x] 3.2 Implement shared validator behavior for environment URLs, missing-service startup/readiness, fixed viewport/theme/locale/DPR, font readiness and deterministic animation/caret handling.
- [x] 3.3 Implement `scripts/ui/validate-tabler-typography.mjs` for Fixture computed-style, CDP rendered-font, bounding-box, screenshot/pixel diff, network and console gates with JSON/image artifacts.
- [x] 3.4 Implement `scripts/ui/audit-page-typography.mjs` for real Capture/Timeline/Search/Ask/Settings page typography and overflow/error checks.

## 4. Automated validation and iteration

- [x] 4.1 Run the unified validator against the official Tabler Reference and StarMem at all four viewports and both themes; analyze and fix any typography-only failures.
- [x] 4.2 Run the existing Web build, lint, smoke/traversal and relevant API regression checks; confirm no layout, composition or business behavior changes.

## 5. Final evidence and handoff

- [x] 5.1 Verify all required JSON, reference/StarMem/diff screenshots and exit-code evidence exist under `artifacts/ui/`.
- [x] 5.2 Write `docs/ui/STARMEM_TABLER_TYPOGRAPHY_REPORT.md` with official/current stacks, rendered fonts, computed/bounding-box/screenshot/network/console results, light/dark/mobile results and remaining deviations.
- [x] 5.3 Validate OpenSpec, mark all tasks complete, and update `docs/DEVELOPMENT_STATUS.md` with actual commands/results and any honest limitations.
