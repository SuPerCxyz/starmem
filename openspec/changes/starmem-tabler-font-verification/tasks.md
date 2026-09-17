## 1. Source and current-state evidence

- [x] 1.1 Reconfirm the pinned Tabler source, actual build/preview commands, official font tokens, and current Reference/StarMem URLs; record the starting runtime cascade and font/network state.
- [x] 1.2 Audit current fixture coverage and existing validator behavior against the new required samples and artifact names; preserve compatible behavior.

## 2. Strict verification implementation

- [x] 2.1 Add the non-navigated `/__ui/tabler-font-fixture` alias using the existing production fixture markup and no test-only typography override.
- [x] 2.2 Add strict per-node sample definitions for Latin, numbers, UUID/technical text, CJK, mixed text, and monospace, including CDP platform-font comparison and CJK stability rules.
- [x] 2.3 Add `scripts/ui/verify-tabler-rendered-fonts.mjs` and write `artifacts/ui/fonts/tabler-rendered-fonts.json`, `starmem-rendered-fonts.json`, and `rendered-font-diff.json`.
- [x] 2.4 Add computed-style, bounding-box, screenshot, font-network, console, overflow, light/dark, and fixed viewport gates under `artifacts/ui/fonts/`.
- [x] 2.5 Add real-page typography output at `artifacts/ui/fonts/real-page-font-audit.json` and package scripts `ui:verify-fonts`, `ui:audit-fonts`, and `ui:verify-tabler-fonts`.

## 3. Documentation and verification

- [x] 3.1 Record the official-stack cascade/root cause and source mapping without modifying Tabler vendor CSS.
- [x] 3.2 Run the new verifier, inspect JSON and PNG diffs, and iterate on typography-only failures until the strict command exits 0.
- [x] 3.3 Run Web lint/build, API regression, smoke/traversal/composition checks, and confirm the no-layout/no-business-change boundary.
- [x] 3.4 Write `docs/ui/STARMEM_TABLER_FONT_VERIFICATION_REPORT.md` with per-node rendered-font results, computed/geometry/screenshot/network/console results, root cause, changed files, and limitations.
- [x] 3.5 Verify retained artifacts, validate OpenSpec, update `docs/DEVELOPMENT_STATUS.md`, and leave services at the product default configuration.

## 4. Official-stack revision

- [x] 4.1 Remove the custom CJK font suffix from StarMem and require exact Tabler Reference family matching in every validator.
- [x] 4.2 Update the deviation/audit/report documents to state that no custom CJK fallback is used.
- [x] 4.3 Rebuild and rerun the strict rendered-font, real-page, compatibility, and relevant regression checks until the final exit codes are successful.
