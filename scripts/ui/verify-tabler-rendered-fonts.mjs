import { mkdir } from "node:fs/promises";
import path from "node:path";
import {
  ARTIFACT_ROOT,
  BOX_TOLERANCE,
  PIXEL_DIFF_MAX_RATIO,
  STYLE_PROPERTIES,
  THEMES,
  VIEWPORTS,
  compareFontFamily,
  ensureServices,
  flattenFamilies,
  launchBrowser,
  loadConfig,
  newAuditContext,
  networkAndConsoleResult,
  openFixture,
  pixelDiff,
  writeJson,
} from "./typography-utils.mjs";

const FONT_ARTIFACT_ROOT = path.join(ARTIFACT_ROOT, "fonts");
const REFERENCE_DIR = path.join(FONT_ARTIFACT_ROOT, "reference");
const STARMEM_DIR = path.join(FONT_ARTIFACT_ROOT, "starmem");
const DIFF_DIR = path.join(FONT_ARTIFACT_ROOT, "diff");
const STARMEM_FIXTURE_PATH = "/__ui/tabler-font-fixture";

const SAMPLES = [
  { id: "latin-title", kind: "latin", selector: "#fixture-brand" },
  { id: "latin-search", kind: "latin", selector: "#fixture-latin-search" },
  { id: "latin-settings", kind: "latin", selector: "#fixture-latin-settings" },
  { id: "latin-inbox", kind: "latin", selector: "#fixture-latin-inbox" },
  { id: "number", kind: "number", selector: "#fixture-number" },
  { id: "uuid", kind: "uuid", selector: "#fixture-uuid" },
  { id: "technical", kind: "technical", selector: "#fixture-technical" },
  { id: "cjk-title", kind: "cjk", selector: "#fixture-page-title" },
  { id: "cjk-navigation", kind: "cjk", selector: "#fixture-nav-timeline" },
  { id: "cjk-body", kind: "cjk", selector: "#fixture-chinese" },
  { id: "cjk-button", kind: "cjk", selector: "#fixture-button" },
  { id: "cjk-input", kind: "cjk", selector: "#fixture-cjk-input" },
  { id: "cjk-select", kind: "cjk", selector: "#fixture-select" },
  { id: "cjk-badge", kind: "cjk", selector: "#fixture-badge" },
  { id: "cjk-status", kind: "cjk", selector: "#fixture-status" },
  { id: "mixed", kind: "mixed", selector: "#fixture-mixed" },
  { id: "monospace-code", kind: "monospace", selector: "#fixture-code" },
  { id: "monospace-pre", kind: "monospace", selector: "#fixture-code-small" },
];
const BOX_SAMPLE_IDS = new Set([
  "cjk-title",
  "cjk-navigation",
  "cjk-button",
  "cjk-input",
  "cjk-badge",
  "cjk-body",
  "monospace-code",
]);

function normalize(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function familyNames(platformFonts) {
  return (platformFonts?.fonts ?? []).map((font) => font.familyName);
}

function cjkFamily(name) {
  return /cjk|noto sans sc|yahei/i.test(name);
}

function cjkFamilies(platformFonts) {
  return familyNames(platformFonts).filter(cjkFamily);
}

function latinFamilies(platformFonts) {
  return familyNames(platformFonts).filter((name) => !cjkFamily(name));
}

function primaryLatin(platformFonts) {
  return latinFamilies(platformFonts)[0] ?? null;
}

async function collectNodes(page) {
  return page.evaluate(({ samples, properties }) => Object.fromEntries(samples.map((sample) => {
    const element = document.querySelector(sample.selector);
    if (!element) return [sample.id, null];
    const style = getComputedStyle(element);
    let text = element.innerText ?? element.textContent ?? "";
    if (element instanceof HTMLSelectElement) text = Array.from(element.selectedOptions).map((option) => option.text).join(" ");
    else if ("value" in element && element.value) text = element.value;
    const rect = element.getBoundingClientRect();
    return [sample.id, {
      selector: sample.selector,
      tagName: element.tagName,
      text: String(text).replace(/\s+/g, " ").trim(),
      styles: Object.fromEntries(properties.map((property) => [property, style[property]])),
      box: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
    }];
  })), { samples: SAMPLES, properties: STYLE_PROPERTIES });
}

async function collectPlatformFontsBySample(page) {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("DOM.enable");
  await cdp.send("CSS.enable");
  const result = {};
  try {
    const documentNode = await cdp.send("DOM.getDocument", { depth: -1 });
    for (const sample of SAMPLES) {
      const query = await cdp.send("DOM.querySelector", { nodeId: documentNode.root.nodeId, selector: sample.selector });
      result[sample.id] = query.nodeId ? await cdp.send("CSS.getPlatformFontsForNode", { nodeId: query.nodeId }) : null;
    }
  } finally {
    await cdp.detach();
  }
  return result;
}

async function collectDocumentFontState(page) {
  return page.evaluate(() => {
    const body = getComputedStyle(document.body);
    return {
      status: document.fonts.status,
      checks: {
        inter: document.fonts.check("14px Inter"),
        interVariable: document.fonts.check("14px InterVariable"),
        notoSansSc: document.fonts.check("14px Noto Sans SC"),
      },
      body: {
        fontFamily: body.fontFamily,
        fontSize: body.fontSize,
        fontWeight: body.fontWeight,
        lineHeight: body.lineHeight,
        letterSpacing: body.letterSpacing,
        fontFeatureSettings: body.fontFeatureSettings,
      },
    };
  });
}

async function makeSideEvidence(page, events, viewport, theme, platformFonts) {
  const nodes = await collectNodes(page);
  return {
    viewport,
    theme,
    documentFonts: await collectDocumentFontState(page),
    samples: Object.fromEntries(SAMPLES.map((sample) => {
      const node = nodes[sample.id];
      return [sample.id, {
        sample: sample.id,
        kind: sample.kind,
        selector: sample.selector,
        text: node?.text ?? "",
        tagName: node?.tagName ?? null,
        styles: node?.styles ?? null,
        box: node?.box ?? null,
        platformFonts: flattenFamilies({ sample: platformFonts[sample.id] }).sample ?? [],
      }];
    })),
    browser: networkAndConsoleResult(events),
  };
}

function compareStyles(reference, starmem) {
  const differences = [];
  for (const sample of SAMPLES) {
    const expected = reference.samples[sample.id];
    const actual = starmem.samples[sample.id];
    if (!expected || !actual) {
      differences.push({ sample: sample.id, property: "node", reference: Boolean(expected), starmem: Boolean(actual) });
      continue;
    }
    for (const property of STYLE_PROPERTIES) {
      if (property === "fontFamily") {
        const comparison = compareFontFamily(expected.styles[property], actual.styles[property]);
        if (!comparison.pass) differences.push({ sample: sample.id, property, reference: expected.styles[property], starmem: actual.styles[property], detail: comparison });
      } else if (normalize(expected.styles[property]) !== normalize(actual.styles[property])) {
        differences.push({ sample: sample.id, property, reference: expected.styles[property], starmem: actual.styles[property] });
      }
    }
  }
  return { pass: differences.length === 0, differences };
}

function compareDimensions(reference, starmem) {
  const differences = [];
  for (const sample of SAMPLES.filter((item) => BOX_SAMPLE_IDS.has(item.id))) {
    const expected = reference.samples[sample.id]?.box;
    const actual = starmem.samples[sample.id]?.box;
    if (!expected || !actual) {
      differences.push({ sample: sample.id, reference: expected, starmem: actual });
      continue;
    }
    for (const property of ["width", "height"]) {
      const delta = Math.abs(expected[property] - actual[property]);
      if (delta > BOX_TOLERANCE) differences.push({ sample: sample.id, property, reference: expected[property], starmem: actual[property], delta });
    }
  }
  return { pass: differences.length === 0, differences, tolerance: BOX_TOLERANCE };
}

function compareRenderedFonts(reference, starmem) {
  const differences = [];
  const checks = [];
  for (const sample of SAMPLES) {
    const expected = reference.samples[sample.id];
    const actual = starmem.samples[sample.id];
    const referenceFonts = expected?.platformFonts ?? [];
    const starmemFonts = actual?.platformFonts ?? [];
    const referenceNames = referenceFonts.map((font) => font.familyName);
    const starmemNames = starmemFonts.map((font) => font.familyName);
    let pass = Boolean(expected && actual && referenceNames.length && starmemNames.length);
    let reason = "";
    if (pass && sample.kind === "cjk") {
      pass = JSON.stringify(referenceFonts) === JSON.stringify(starmemFonts);
      reason = "exact Tabler Reference CJK platform-font list";
    } else if (pass && sample.kind === "mixed") {
      pass = JSON.stringify(referenceFonts) === JSON.stringify(starmemFonts);
      reason = "exact mixed Latin/CJK platform-font list";
    } else if (pass && sample.kind === "monospace") {
      pass = referenceNames.join("|") === starmemNames.join("|");
      reason = "exact monospace platform-font list";
    } else if (pass) {
      pass = primaryLatin({ fonts: referenceFonts }) === primaryLatin({ fonts: starmemFonts });
      reason = "exact primary Latin platform font";
    }
    const check = {
      sample: sample.id,
      kind: sample.kind,
      text: expected?.text ?? actual?.text ?? "",
      reference: referenceFonts,
      starmem: starmemFonts,
      pass,
      reason,
    };
    checks.push(check);
    if (!pass) differences.push(check);
  }
  const starmemCjk = new Set(SAMPLES.filter((sample) => sample.kind === "cjk" || sample.kind === "mixed").flatMap((sample) => cjkFamilies({ fonts: starmem.samples[sample.id]?.platformFonts ?? [] })));
  const stability = {
    sample: "cjk-stability",
    reference: [...new Set(SAMPLES.filter((sample) => sample.kind === "cjk" || sample.kind === "mixed").flatMap((sample) => cjkFamilies({ fonts: reference.samples[sample.id]?.platformFonts ?? [] })))],
    starmem: [...starmemCjk],
    pass: starmemCjk.size === 1 && [...starmemCjk].sort().join("|") === [...new Set(SAMPLES.filter((sample) => sample.kind === "cjk" || sample.kind === "mixed").flatMap((sample) => cjkFamilies({ fonts: reference.samples[sample.id]?.platformFonts ?? [] })))].sort().join("|"),
    reason: "one exact CJK family across Reference and StarMem title/navigation/body/button/input/select/badge/status/mixed",
  };
  checks.push(stability);
  if (!stability.pass) differences.push(stability);
  return { pass: differences.length === 0, checks, differences };
}

async function main() {
  const config = await loadConfig();
  await Promise.all([mkdir(REFERENCE_DIR, { recursive: true }), mkdir(STARMEM_DIR, { recursive: true }), mkdir(DIFF_DIR, { recursive: true })]);
  const generatedAt = new Date().toISOString();
  const referenceArtifact = { generatedAt, target: "Tabler Reference", url: config.tablerUrl, combinations: [] };
  const starmemArtifact = { generatedAt, target: "StarMem", url: config.starmemUrl, fixturePath: STARMEM_FIXTURE_PATH, combinations: [] };
  const renderedDiff = { generatedAt, referenceUrl: config.tablerUrl, starmemUrl: config.starmemUrl, samples: SAMPLES, combinations: [] };
  const computedDiff = { generatedAt, properties: STYLE_PROPERTIES, combinations: [] };
  const boundingBoxDiff = { generatedAt, tolerance: BOX_TOLERANCE, combinations: [] };
  let cleanupServices;
  let browser;
  let fatalError = null;

  try {
    cleanupServices = await ensureServices(config);
    browser = await launchBrowser();
    for (const viewport of VIEWPORTS) {
      for (const theme of THEMES) {
        const referenceContext = await newAuditContext(browser, viewport, theme);
        const starmemContext = await newAuditContext(browser, viewport, theme);
        const key = `${viewport.width}x${viewport.height}-${theme}`;
        const referencePath = path.join(REFERENCE_DIR, `font-reference-${key}.png`);
        const starmemPath = path.join(STARMEM_DIR, `font-starmem-${key}.png`);
        const diffPath = path.join(DIFF_DIR, `font-diff-${key}.png`);
        try {
          await openFixture(referenceContext.page, config.tablerUrl, theme, true);
          await openFixture(starmemContext.page, config.starmemUrl, theme, false, STARMEM_FIXTURE_PATH);
          const referenceFonts = await (async () => collectPlatformFontsBySample(referenceContext.page))();
          const starmemFonts = await (async () => collectPlatformFontsBySample(starmemContext.page))();
          const reference = await makeSideEvidence(referenceContext.page, referenceContext.events, viewport, theme, referenceFonts);
          const starmem = await makeSideEvidence(starmemContext.page, starmemContext.events, viewport, theme, starmemFonts);
          await referenceContext.page.locator("#typography-fixture-root").screenshot({ path: referencePath });
          await starmemContext.page.locator("#typography-fixture-root").screenshot({ path: starmemPath });
          const screenshot = await pixelDiff(referencePath, starmemPath, diffPath);
          const styles = compareStyles(reference, starmem);
          const dimensions = compareDimensions(reference, starmem);
          const fonts = compareRenderedFonts(reference, starmem);
          const result = {
            key,
            viewport,
            theme,
            pass: fonts.pass && styles.pass && dimensions.pass && screenshot.pass && reference.browser.pass && starmem.browser.pass,
            fonts,
            styles,
            dimensions,
            screenshot,
            browser: { reference: reference.browser, starmem: starmem.browser },
          };
          referenceArtifact.combinations.push(reference);
          starmemArtifact.combinations.push(starmem);
          renderedDiff.combinations.push({ key, viewport, theme, checks: fonts.checks, pass: fonts.pass });
          computedDiff.combinations.push({ key, viewport, theme, ...styles });
          boundingBoxDiff.combinations.push({ key, viewport, theme, ...dimensions });
          if (!result.pass) console.error(`Rendered font verification failed: ${key}`);
          renderedDiff.combinations.at(-1).screenshot = screenshot;
          renderedDiff.combinations.at(-1).browser = { reference: reference.browser, starmem: starmem.browser };
          renderedDiff.combinations.at(-1).pass = result.pass;
        } catch (error) {
          const failure = { key, viewport, theme, pass: false, error: String(error) };
          referenceArtifact.combinations.push(failure);
          starmemArtifact.combinations.push(failure);
          renderedDiff.combinations.push(failure);
          computedDiff.combinations.push(failure);
          boundingBoxDiff.combinations.push(failure);
          console.error(`Rendered font verification failed: ${key}`);
        } finally {
          await referenceContext.context.close();
          await starmemContext.context.close();
        }
      }
    }
  } catch (error) {
    fatalError = String(error);
    console.error(fatalError);
  } finally {
    await writeJson(path.join(FONT_ARTIFACT_ROOT, "tabler-rendered-fonts.json"), { ...referenceArtifact, fatalError });
    await writeJson(path.join(FONT_ARTIFACT_ROOT, "starmem-rendered-fonts.json"), { ...starmemArtifact, fatalError });
    await writeJson(path.join(FONT_ARTIFACT_ROOT, "rendered-font-diff.json"), { ...renderedDiff, fatalError });
    await writeJson(path.join(FONT_ARTIFACT_ROOT, "computed-style-diff.json"), { ...computedDiff, fatalError });
    await writeJson(path.join(FONT_ARTIFACT_ROOT, "bounding-box-diff.json"), { ...boundingBoxDiff, fatalError });
    if (browser) await browser.close();
    if (cleanupServices) await cleanupServices();
  }

  const failed = fatalError || renderedDiff.combinations.some((item) => !item.pass);
  if (failed) {
    console.error("Tabler rendered-font verification: FAIL");
    process.exitCode = 1;
    return;
  }
  console.log(`Tabler rendered-font verification: PASS (${renderedDiff.combinations.length} combinations; ${SAMPLES.length} samples)`);
}

main().catch((error) => {
  console.error(String(error));
  process.exitCode = 1;
});
