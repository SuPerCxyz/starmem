import path from "node:path";
import { ARTIFACT_ROOT, STYLE_PROPERTIES, THEMES, VIEWPORTS, compareFontFamily, collectPlatformFonts, ensureServices, launchBrowser, loadConfig, newAuditContext, networkAndConsoleResult, openFixture, writeJson } from "./typography-utils.mjs";

const ROUTES = [
  { path: "/capture", name: "capture" },
  { path: "/timeline", name: "timeline" },
  { path: "/search", name: "search" },
  { path: "/ask", name: "ask" },
  { path: "/settings", name: "settings" },
];
const PAGE_SELECTORS = {
  body: "body",
  pageTitle: ".page-title",
  nav: ".navbar-vertical .navbar-nav .nav-item:not(.active) .nav-link",
  formControl: ".form-control",
  button: ".btn-primary, .btn:not(.btn-link)",
  badge: ".badge",
  description: ".page-header .text-secondary, .page-header p",
  status: ".status",
  code: "pre, code",
  table: "table td",
};

function normalize(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

async function collectNodes(page, selectors) {
  return page.evaluate(({ selectors, properties }) => Object.fromEntries(Object.entries(selectors).map(([name, selector]) => {
    const element = document.querySelector(selector);
    if (!element) return [name, null];
    const style = getComputedStyle(element);
    return [name, {
      selector,
      tagName: element.tagName,
      className: typeof element.className === "string" ? element.className : "",
      parentClassName: typeof element.parentElement?.className === "string" ? element.parentElement.className : "",
      visible: Boolean(element.getClientRects().length),
      styles: Object.fromEntries(properties.map((property) => [property, style[property]])),
    }];
  })), { selectors, properties: STYLE_PROPERTIES });
}

async function collectReferenceExpectations(page) {
  const ids = {
    body: "body",
    pageTitle: "#fixture-page-title",
    nav: "#fixture-nav-timeline",
    navButton: "#fixture-nav-button",
    formControl: "#fixture-input",
    button: "#fixture-button",
    badge: "#fixture-badge",
    badgeButton: "#fixture-badge-button",
    description: "#fixture-subtitle",
    status: "#fixture-status",
    statusButton: "#fixture-status-button",
    code: "#fixture-code",
    codeInline: "#fixture-code-inline",
    codeSmall: "#fixture-code-small",
    codeButton: "#fixture-code-button",
    table: "#fixture-table-cell",
  };
  return page.evaluate(({ ids, properties }) => Object.fromEntries(Object.entries(ids).map(([name, selector]) => {
    const element = document.querySelector(selector);
    if (!element) return [name, null];
    const style = getComputedStyle(element);
    return [name, Object.fromEntries(properties.map((property) => [property, style[property]]))];
  })), { ids, properties: STYLE_PROPERTIES });
}

function compareNodeStyles(expected, actual) {
  if (!actual) return { pass: true, present: false, differences: [] };
  if (!expected) return { pass: false, present: true, differences: [{ property: "reference-node", reference: false, starmem: true }] };
  const differences = [];
  for (const property of STYLE_PROPERTIES) {
    if (property === "fontFamily") {
      const comparison = compareFontFamily(expected[property], actual.styles[property]);
      if (!comparison.pass) differences.push({ property, reference: expected[property], starmem: actual.styles[property], detail: comparison });
    } else if (normalize(expected[property]) !== normalize(actual.styles[property])) {
      differences.push({ property, reference: expected[property], starmem: actual.styles[property] });
    }
  }
  return { pass: differences.length === 0, present: true, differences };
}

async function login(page, config, events) {
  await page.goto(config.starmemUrl + "/capture", { waitUntil: "networkidle" });
  if (await page.getByRole("heading", { name: "欢迎回到 StarMem" }).isVisible()) {
    if (!config.email || !config.password) throw new Error("STARMEM_TEST_EMAIL/PASSWORD or admin credentials are required for real-page audit.");
    await page.getByLabel("邮箱").fill(config.email);
    await page.getByLabel("密码").fill(config.password);
    await page.getByRole("button", { name: "登录 StarMem" }).click();
  }
  await page.getByLabel("记录内容").waitFor({ timeout: 30000 });
  events.consoleErrors.length = 0;
  events.pageErrors.length = 0;
  events.fontRequests.length = 0;
  events.fontResponses.length = 0;
  events.fontFailures.length = 0;
}

async function main() {
  const config = await loadConfig();
  let cleanupServices;
  let browser;
  const audit = {
    generatedAt: new Date().toISOString(),
    referenceUrl: config.tablerUrl,
    starmemUrl: config.starmemUrl,
    routes: ROUTES,
    viewports: VIEWPORTS,
    themes: THEMES,
    properties: STYLE_PROPERTIES,
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
        try {
          await openFixture(reference.page, config.tablerUrl, theme, true);
          const expected = await collectReferenceExpectations(reference.page);
          await login(starmem.page, config, starmem.events);
          for (const route of ROUTES) {
            await starmem.page.goto(config.starmemUrl + route.path, { waitUntil: "networkidle" });
            await starmem.page.waitForSelector(".page-title", { timeout: 30000 });
            await starmem.page.waitForTimeout(200);
            await starmem.page.evaluate(async () => {
              await document.fonts.ready;
              if (document.fonts.status !== "loaded") throw new Error("document.fonts did not reach loaded state");
            });
            await starmem.page.evaluate((selectedTheme) => {
              document.documentElement.lang = "zh-CN";
              document.documentElement.setAttribute("data-bs-theme", selectedTheme);
            }, theme);
            const actual = await collectNodes(starmem.page, PAGE_SELECTORS);
            const comparisons = Object.fromEntries(Object.entries(actual).map(([name, node]) => {
              const expectedNode = name === "nav" ? expected.navButton : name === "badge" && node?.tagName === "BUTTON" ? expected.badgeButton : name === "status" && node?.tagName === "BUTTON" ? expected.statusButton : name === "code" && node?.parentClassName?.split(/\s+/).includes("btn") ? expected.codeButton : name === "code" && node?.tagName === "CODE" ? expected.codeInline : name === "code" && node?.className.split(/\s+/).includes("small") ? expected.codeSmall : expected[name];
              return [name, compareNodeStyles(expectedNode, node)];
            }));
            const platformFonts = await collectPlatformFonts(starmem.page, {
              body: "body",
              pageTitle: ".page-title",
              nav: ".navbar-vertical .navbar-nav .nav-item:not(.active) .nav-link",
              code: "pre, code",
            });
            const overflow = await starmem.page.evaluate(() => ({
              scrollWidth: document.documentElement.scrollWidth,
              clientWidth: document.documentElement.clientWidth,
              overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
            }));
            const browserResult = networkAndConsoleResult(starmem.events);
            const result = {
              route: route.path,
              name: route.name,
              viewport,
              theme,
              actual,
              comparisons,
              platformFonts,
              overflow,
              browser: browserResult,
              pass: Object.values(comparisons).every((item) => item.pass) && overflow.overflow === 0 && browserResult.pass,
            };
            audit.combinations.push(result);
            if (!result.pass) console.error("Page typography failed: " + route.path + " " + String(viewport.width) + "x" + String(viewport.height) + "-" + theme);
          }
        } finally {
          await reference.context.close();
          await starmem.context.close();
        }
      }
    }
  } catch (error) {
    fatalError = String(error);
    console.error(fatalError);
  } finally {
    const output = { ...audit, fatalError };
    await writeJson(path.join(ARTIFACT_ROOT, "page-typography-audit.json"), output);
    await writeJson(path.join(ARTIFACT_ROOT, "fonts", "real-page-font-audit.json"), output);
    if (browser) await browser.close();
    if (cleanupServices) await cleanupServices();
  }

  if (fatalError || audit.combinations.some((item) => !item.pass)) {
    console.error("StarMem page typography audit: FAIL");
    process.exitCode = 1;
    return;
  }
  console.log("StarMem page typography audit: PASS (" + audit.combinations.length + " page combinations)");
}

main().catch((error) => {
  console.error(String(error));
  process.exitCode = 1;
});
