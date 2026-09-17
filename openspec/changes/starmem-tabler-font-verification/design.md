## Context

See `proposal.md`. StarMem already has a shared Tabler fixture and a first-generation typography validator in the completed `starmem-tabler-typography` change. The revised contract requires the production page and validator to inherit the pinned Tabler stack exactly, without appending a custom CJK family.

## Goals / Non-Goals

**Goals:**

- Reuse the existing deterministic fixture and browser helpers where they already provide the required behavior.
- Inherit the pinned Tabler sans and monospace stacks exactly, with no StarMem CJK suffix or other custom font family.
- Add a strict node-level CDP rendered-font comparison for Latin, number, UUID, CJK, mixed, and monospace samples.
- Keep the Tabler source pinned and use environment-provided Reference/StarMem URLs.
- Preserve all JSON/PNG evidence and make the unified command return an authoritative exit code.

**Non-Goals:**

- No layout, component composition, business/API, database, worker, vendor CSS, or production typography redesign.
- No Inter download or test-only font override when the pinned Tabler source uses system fonts.
- No screenshot mask, hidden target content, relaxed threshold, or visual inline style.

## Decisions

- **Extend rather than duplicate the fixture:** make `/__ui/tabler-font-fixture` an alias of the existing fixture component and keep the original route/scripts for backward compatibility. This gives the new contract its requested stable name without two sources of test text.
- **Share the existing Playwright utilities:** add only the new strict verifier and artifact adapters around the existing browser/CDP helpers. This avoids a second service lifecycle, browser discovery, or CJK-family policy implementation.
- **Keep the pinned system stack exactly:** use the current Tabler source as the first-order authority. The current build has `$font-google: null`, so the actual host fonts reported by CDP—not `document.fonts.check()`—are the comparison evidence. CJK is compared exactly with the Reference; no fallback suffix is added by StarMem.
- **Use node-level samples instead of whole-page semantics:** each sample gets a stable ID, text, platform-font result, computed styles, and bounding box. Whole-fixture screenshots remain a secondary regression gate; the fixture element is captured without unrelated Preview chrome.
- **Use fixed paths and environment URLs:** write rendered-font inputs/outputs to `artifacts/ui/fonts/`, load `TABLER_REFERENCE_URL` and `STARMEM_URL` from the environment/config, and keep the existing temporary QA rate-limit procedure outside product configuration for real-page runs.

## Risks / Trade-offs

- [Host system fonts vary] → record the exact platform fonts and run both targets in the same Chromium context settings; strict comparison is intentionally host-specific and catches any CJK difference instead of adding a custom fallback.
- [Existing validator and new verifier can drift] → share selectors, fixture markup, style properties, tolerances, and service helpers; run both compatibility and new commands before handoff.
- [Real-page audit can exceed the product rate limit] → use an external, temporary Compose QA override only for the audit run, delete it afterward, and verify the product remains at 120 req/min.
- [Reference Preview dev chrome can overlap screenshots] → remove only the Preview-only element outside the copied fixture before capture; do not mask or alter fixture nodes.
