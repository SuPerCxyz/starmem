import path from "node:path";
import { ARTIFACT_ROOT, BOX_TOLERANCE, FONT_SELECTORS, PIXEL_DIFF_MAX_RATIO, STYLE_PROPERTIES, STYLE_SELECTORS, THEMES, VIEWPORTS, collectBoxes, collectComputedStyles, collectPlatformFonts, compareFontFamily as compareFamily, ensureServices, flattenFamilies, launchBrowser, loadConfig, newAuditContext, networkAndConsoleResult, openFixture, pixelDiff, writeJson } from "./typography-utils.mjs";

const referenceDir = path.join(ARTIFACT_ROOT, "reference");
const starmemDir = path.join(ARTIFACT_ROOT, "starmem");
const diffDir = path.join(ARTIFACT_ROOT, "diff");

function compareStyles(reference, starmem) {
  const differences = [];
  for (const selector of STYLE_SELECTORS) {
    const expected = reference[selector];
    const actual = starmem[selector];
    if (!expected || !actual) {
      differences.push({ selector, property: "node", reference: Boolean(expected), starmem: Boolean(actual) });
      continue;
    }
    for (const property of STYLE_PROPERTIES) {
      if (property === "fontFamily") {
        const comparison = compareFamily(expected[property], actual[property]);
        if (!comparison.pass) differences.push({ selector, property, reference: expected[property], starmem: actual[property], detail: comparison });
      } else if (String(expected[property]).replace(/\s+/g, " ").trim() !== String(actual[property]).replace(/\s+/g, " ").trim()) {
        differences.push({ selector, property, reference: expected[property], starmem: actual[property] });
      }
    }
  }
  return { pass: differences.length === 0, differences };
}

function compareBoxes(reference, starmem) {
  const differences = [];
  for (const [selector, expected] of Object.entries(reference)) {
    const actual = starmem[selector];
    if (!expected || !actual) {
      differences.push({ selector, reference: expected, starmem: actual });
      continue;
    }
    for (const property of ["x", "y", "width", "height"]) {
      const delta = Math.abs(expected[property] - actual[property]);
      if (delta > BOX_TOLERANCE) differences.push({ selector, property, reference: expected[property], starmem: actual[property], delta });
    }
  }
  return { pass: differences.length === 0, differences, tolerance: BOX_TOLERANCE };
}

function familyNames(value) {
  return (value?.fonts ?? []).map((font) => font.familyName);
}

function primaryFamily(value) {
  return familyNames(value)[0] ?? null;
}

function cjkFamilies(value) {
  return familyNames(value).filter((family) => /cjk|noto sans sc|yahei/i.test(family));
}

function compareRenderedFonts(reference, starmem) {
  const checks = [];
  for (const sample of ["latin", "number", "monospace"]) {
    const expected = primaryFamily(reference[sample]);
    const actual = primaryFamily(starmem[sample]);
    checks.push({ sample, reference: expected, starmem: actual, pass: expected !== null && expected === actual });
  }
  const referenceCjk = new Set([...cjkFamilies(reference.chinese), ...cjkFamilies(reference.mixed)]);
  const starmemCjk = new Set([...cjkFamilies(starmem.chinese), ...cjkFamilies(starmem.mixed)]);
  checks.push({
    sample: "chinese/mixed",
    reference: [...referenceCjk],
    starmem: [...starmemCjk],
    pass: starmemCjk.size > 0 && [...referenceCjk].sort().join("|") === [...starmemCjk].sort().join("|"),
    allowed: "none; exact Tabler Reference CJK family required",
  });
  return { pass: checks.every((check) => check.pass), checks };
}

async function collectOverflow(page) {
  return page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  }));
}

async function main() {
  const config = await loadConfig();
  let cleanupServices;
  let browser;
  const styleDiff = {
    generatedAt: new Date().toISOString(),
    referenceUrl: config.tablerUrl,
    starmemUrl: config.starmemUrl,
    viewports: VIEWPORTS,
    themes: THEMES,
    properties: STYLE_PROPERTIES,
    selectors: STYLE_SELECTORS,
    maxPixelDiffRatio: PIXEL_DIFF_MAX_RATIO,
    combinations: [],
  };
  const renderedFonts = {
    generatedAt: styleDiff.generatedAt,
    referenceUrl: config.tablerUrl,
    starmemUrl: config.starmemUrl,
    combinations: [],
  };
  let fatalError = null;

  try {
    cleanupServices = await ensureServices(config);
    browser = await launchBrowser();
    for (const viewport of VIEWPORTS) {
      for (const theme of THEMES) {
        const reference = await newAuditContext(browser, viewport, theme);
        const starmem = await newAuditContext(browser, viewport, theme);
        const key = String(viewport.width) + "x" + String(viewport.height) + "-" + theme;
        const referencePath = path.join(referenceDir, "typography-reference-" + key + ".png");
        const starmemPath = path.join(starmemDir, "typography-starmem-" + key + ".png");
        const diffPath = path.join(diffDir, "typography-diff-" + key + ".png");
        let result;
        try {
          await openFixture(reference.page, config.tablerUrl, theme, true);
          await openFixture(starmem.page, config.starmemUrl, theme, false);
          const referenceStyles = await collectComputedStyles(reference.page);
          const starmemStyles = await collectComputedStyles(starmem.page);
          const referenceBoxes = await collectBoxes(reference.page);
          const starmemBoxes = await collectBoxes(starmem.page);
          const referenceFonts = await collectPlatformFonts(reference.page, FONT_SELECTORS);
          const starmemFonts = await collectPlatformFonts(starmem.page, FONT_SELECTORS);
          await reference.page.locator("#typography-fixture-root").screenshot({ path: referencePath });
          await starmem.page.locator("#typography-fixture-root").screenshot({ path: starmemPath });
          const screenshot = await pixelDiff(referencePath, starmemPath, diffPath);
          const styles = compareStyles(referenceStyles, starmemStyles);
          const boxes = compareBoxes(referenceBoxes, starmemBoxes);
          const fonts = compareRenderedFonts(referenceFonts, starmemFonts);
          const referenceNetwork = networkAndConsoleResult(reference.events);
          const starmemNetwork = networkAndConsoleResult(starmem.events);
          const referenceOverflow = await collectOverflow(reference.page);
          const starmemOverflow = await collectOverflow(starmem.page);
          result = {
            key,
            viewport,
            theme,
            styles,
            boxes,
            screenshot,
            overflow: { reference: referenceOverflow, starmem: starmemOverflow },
            browser: { reference: referenceNetwork, starmem: starmemNetwork },
            pass: styles.pass && fonts.pass && boxes.pass && screenshot.pass && referenceNetwork.pass && starmemNetwork.pass && referenceOverflow.overflow === 0 && starmemOverflow.overflow === 0,
          };
          styleDiff.combinations.push(result);
          renderedFonts.combinations.push({ key, viewport, theme, reference: flattenFamilies(referenceFonts), starmem: flattenFamilies(starmemFonts), comparison: fonts });
        } catch (error) {
          result = { key, viewport, theme, pass: false, error: String(error) };
          styleDiff.combinations.push(result);
          renderedFonts.combinations.push(result);
        } finally {
          await reference.context.close();
          await starmem.context.close();
        }
        if (!result.pass) console.error("Typography fixture failed: " + key);
      }
    }
  } catch (error) {
    fatalError = String(error);
    console.error(fatalError);
  } finally {
    await writeJson(path.join(ARTIFACT_ROOT, "tabler-typography-style-diff.json"), { ...styleDiff, fatalError });
    await writeJson(path.join(ARTIFACT_ROOT, "tabler-rendered-fonts.json"), { ...renderedFonts, fatalError });
    if (browser) await browser.close();
    if (cleanupServices) await cleanupServices();
  }

  const failed = fatalError || styleDiff.combinations.some((item) => !item.pass);
  if (failed) {
    console.error("Tabler typography validation: FAIL");
    process.exitCode = 1;
    return;
  }
  console.log("Tabler typography validation: PASS (" + styleDiff.combinations.length + " fixture combinations)");
}

main().catch((error) => {
  console.error(String(error));
  process.exitCode = 1;
});
