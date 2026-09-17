## ADDED Requirements

### Requirement: Tabler Typography Fidelity

Web Typography MUST use the pinned Tabler official system font stack and typography tokens as its source of truth. StarMem MAY append an explicitly documented CJK fallback because the official Latin stack does not contain complete Chinese glyph coverage, but MUST NOT otherwise override component typography.

#### Scenario: Official typography source
- **WHEN** the pinned Tabler source is inspected
- **THEN** the application records its actual sans stack, monospace stack, body size, body line-height, feature settings, and component typography values before changing them

#### Scenario: No private typography system
- **WHEN** the application source is audited
- **THEN** it contains no unapproved font import, private font scale, visual inline typography style, arbitrary typography value, or page-specific typography override

#### Scenario: Documented CJK deviation
- **WHEN** a CJK fallback is added
- **THEN** `TABLER_DEVIATIONS.md` records the reason and exact fallback order, while font-size, font-weight, line-height, letter-spacing and component spacing remain Tabler-defined

### Requirement: Typography Regression Gate

Typography changes MUST pass the deterministic Reference/StarMem Fixture comparison and real-page typography audit before the change can be declared complete.

#### Scenario: Regression command
- **WHEN** the unified UI validation command runs
- **THEN** it executes Reference availability, StarMem availability, Fixture style/rendered-font/bounding-box/screenshot checks and real-page audit in sequence, returning nonzero on any strong mismatch

#### Scenario: Theme and mobile parity
- **WHEN** the command runs in light/dark and desktop/mobile viewports
- **THEN** typography remains unchanged across themes and no viewport is skipped
