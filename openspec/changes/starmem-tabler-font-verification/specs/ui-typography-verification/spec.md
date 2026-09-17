## Purpose

Provide deterministic browser evidence that StarMem paints text with the same Tabler typography as the pinned official Reference, including actual platform fonts rather than only declared CSS.

## ADDED Requirements

### Requirement: Deterministic font fixture

The system MUST expose `/__ui/tabler-font-fixture` for development and automated verification, MUST keep it out of normal navigation, and MUST render fixed Tabler markup and samples without authentication or API data.

#### Scenario: Fixture is directly accessible

- **WHEN** a browser opens `/__ui/tabler-font-fixture`
- **THEN** it renders the fixed fixture without login, network data, random values, current time, animation, or caret blinking

#### Scenario: Fixture covers required text classes

- **WHEN** the fixture is inspected
- **THEN** it contains title, subtitle, navigation, paragraph, muted text, Latin, numbers, UUID/technical text, CJK, mixed text, button, input, select, badge, status, table, link, code, and pre samples using Tabler DOM/classes

### Requirement: Pinned Tabler typography source

The verification MUST record the pinned Tabler commit, Reference URL, build/dev commands, official sans and monospace stacks, font imports/font-face behavior, CSS variables, and component typography values before judging StarMem.

#### Scenario: Source evidence is recorded

- **WHEN** the verification report is generated
- **THEN** it identifies the actual Tabler source and records body, page title, navbar, form-control, button, badge, table, and code typography without assuming Inter or another font

### Requirement: Actual rendered-font comparison

The verification MUST use Chromium DevTools Protocol platform-font inspection for each required sample on both the Reference and StarMem fixtures, and MUST fail with a non-zero exit code when Latin, numbers, UUID/technical text, or monospace differ from the Reference.

#### Scenario: Latin and technical samples match

- **WHEN** Chromium reports platform fonts for Latin, number, UUID, and technical samples
- **THEN** StarMem's primary rendered font matches the Reference for each sample

#### Scenario: CJK platform font is exact

- **WHEN** Chromium reports platform fonts for CJK, mixed, title, navigation, body, button, badge, and input text
- **THEN** StarMem uses the same CJK platform font list as the Tabler Reference; no CJK family difference is accepted

#### Scenario: Monospace samples match

- **WHEN** Chromium reports platform fonts for `service: starmem`, `openstack volume create`, or a preformatted block
- **THEN** StarMem uses the same rendered monospace family as the Reference

### Requirement: Computed typography and geometry comparison

The verification MUST compare fixture `font-family`, `font-size`, `font-weight`, `font-style`, `line-height`, `letter-spacing`, `font-feature-settings`, and `text-transform`, and MUST compare width/height of key text components within the documented browser rounding tolerance.

#### Scenario: Computed style drift fails

- **WHEN** any required computed typography property differs from the Tabler Reference
- **THEN** the verifier records the node-level difference and exits non-zero

#### Scenario: Component metrics match

- **WHEN** title, navigation text, button, input, badge, body text, and code bounding boxes are compared
- **THEN** their width and height match within the documented tolerance; different page positions do not cause a failure by themselves

### Requirement: Visual and runtime health gates

The verification MUST wait for `document.fonts.ready`, audit font requests and browser errors, compare same-size light/dark screenshots at `1440x1000`, `1920x1080`, `390x844`, and `430x932`, and MUST fail on font request errors, decode/OTS/CORS errors, `console.error`, `pageerror`, unexpected overflow, or a screenshot ratio above the fixed threshold.

#### Scenario: Font network is healthy

- **WHEN** either target requests a font resource
- **THEN** every response is successful with a valid font response and no request failure; zero requests is recorded as valid for a system-font Tabler build

#### Scenario: Reference and StarMem screenshots are retained

- **WHEN** all font and style gates complete
- **THEN** the verifier writes Reference, StarMem, and pixel diff PNGs for every viewport/theme without masking or hiding fixture content

### Requirement: Real page typography audit and artifacts

After the fixture passes, the verification MUST audit `/capture`, `/timeline`, `/search`, `/ask`, and `/settings` for page-level typography overrides and MUST retain node-by-node JSON evidence, style differences, rendered fonts, screenshots, diff images, network/console results, and the final report under the documented artifact paths.

#### Scenario: Real routes have no unexpected override

- **WHEN** the five real pages are opened at all required viewports and themes
- **THEN** body, title, description, navigation, button, input, badge/status, code, and table typography matches the Reference contract, with no unexpected horizontal overflow or browser error

#### Scenario: Validator exit code is authoritative

- **WHEN** any hard gate fails
- **THEN** the command exits non-zero and preserves failure context; when every gate passes it exits zero
