import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import { constants as fsConstants, existsSync, readdirSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";
import { chromium } from "../../web/node_modules/playwright/index.mjs";
import pixelmatch from "../../web/node_modules/pixelmatch/index.js";
import { PNG } from "../../web/node_modules/pngjs/lib/png.js";

export const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
export const TABLER_ROOT = path.join(REPO_ROOT, ".reference", "tabler");
export const FIXTURE_FILE = path.join(REPO_ROOT, "web", "src", "typography-fixture.html");
export const ARTIFACT_ROOT = path.join(REPO_ROOT, "artifacts", "ui");
export const STYLE_PROPERTIES = [
  "fontFamily",
  "fontSize",
  "fontWeight",
  "fontStyle",
  "lineHeight",
  "letterSpacing",
  "fontFeatureSettings",
  "textTransform",
  "textRendering",
];
export const STYLE_SELECTORS = [
  "#fixture-brand",
  "#fixture-page-title",
  "#fixture-subtitle",
  "#fixture-nav-timeline",
  "#fixture-paragraph",
  "#fixture-muted",
  "#fixture-latin",
  "#fixture-number",
  "#fixture-chinese",
  "#fixture-mixed",
  "#fixture-code",
  "#fixture-button",
  "#fixture-input",
  "#fixture-select",
  "#fixture-badge",
  "#fixture-status",
  "#fixture-card-title",
  "#fixture-table-cell",
  "#fixture-small",
  "#fixture-link",
];
export const FONT_SELECTORS = {
  latin: "#fixture-latin",
  number: "#fixture-number",
  chinese: "#fixture-chinese",
  mixed: "#fixture-mixed",
  monospace: "#fixture-code",
};
export const BOX_SELECTORS = [
  "#fixture-page-title",
  "#fixture-nav-timeline",
  "#fixture-button",
  "#fixture-input",
  "#fixture-badge",
  "#fixture-paragraph",
  "#fixture-code",
];
export const VIEWPORTS = [
  { width: 1440, height: 1000 },
  { width: 1920, height: 1080 },
  { width: 390, height: 844 },
  { width: 430, height: 932 },
];
export const THEMES = ["light", "dark"];
// CJK fallback glyphs are intentionally allowed to differ from the Reference host font.
export const PIXEL_DIFF_MAX_RATIO = 0.001;
export const BOX_TOLERANCE = 0.5;
export const FIXTURE_MARKUP = await readFile(FIXTURE_FILE, "utf8");

function parseEnvFile(contents) {
  const values = {};
  for (const line of contents.split(/\r?\n/)) {
    const match = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
    if (!match || match[1].startsWith("#")) continue;
    let value = match[2];
    if (value.length >= 2 && value[0] === value[value.length - 1] && ["'", "\""].includes(value[0])) {
      value = value.slice(1, -1);
    }
    values[match[1]] = value;
  }
  return values;
}

export async function loadConfig() {
  let dotEnv = {};
  try {
    dotEnv = parseEnvFile(await readFile(path.join(REPO_ROOT, ".env"), "utf8"));
  } catch {
    // Environment variables are sufficient in CI.
  }
  const value = (name, fallback = "") => process.env[name] ?? dotEnv[name] ?? fallback;
  const tablerUrl = value("TABLER_REFERENCE_URL");
  const starmemUrl = value("STARMEM_URL");
  if (!tablerUrl || !starmemUrl) {
    throw new Error("TABLER_REFERENCE_URL and STARMEM_URL must be set.");
  }
  return {
    tablerUrl: tablerUrl.replace(/\/+$/, ""),
    starmemUrl: starmemUrl.replace(/\/+$/, ""),
    email: value("STARMEM_TEST_EMAIL", value("STARMEM_ADMIN_EMAIL")),
    password: value("STARMEM_TEST_PASSWORD", value("STARMEM_ADMIN_PASSWORD")),
    tablerStartCommand: value("TABLER_START_COMMAND", "pnpm --filter @tabler/preview dev"),
    starmemStartCommand: value("STARMEM_START_COMMAND", "docker compose up -d"),
    autoStart: value("UI_AUTO_START_SERVICES", "1") !== "0",
  };
}

async function probe(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 2500);
  try {
    const response = await fetch(url, { redirect: "manual", signal: controller.signal });
    return response.status >= 200 && response.status < 400;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

export async function waitForUrl(url, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await probe(url)) return;
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error("Timed out waiting for " + url);
}

function startCommand(command, cwd) {
  const child = spawn(command, {
    cwd,
    env: process.env,
    shell: true,
    stdio: "ignore",
  });
  return child;
}

export async function ensureServices(config) {
  const children = [];
  try {
    if (!(await probe(config.tablerUrl + "/layout-vertical.html"))) {
      if (!config.autoStart) throw new Error("Tabler Reference is unavailable and UI_AUTO_START_SERVICES=0.");
      children.push(startCommand(config.tablerStartCommand, TABLER_ROOT));
    }
    await waitForUrl(config.tablerUrl + "/layout-vertical.html");

    if (!(await probe(config.starmemUrl + "/"))) {
      if (!config.autoStart) throw new Error("StarMem is unavailable and UI_AUTO_START_SERVICES=0.");
      children.push(startCommand(config.starmemStartCommand, REPO_ROOT));
    }
    await waitForUrl(config.starmemUrl + "/");
  } catch (error) {
    await stopChildren(children);
    throw error;
  }
  return async () => stopChildren(children);
}

async function stopChildren(children) {
  for (const child of children) {
    if (child.exitCode === null && !child.killed) child.kill("SIGTERM");
  }
  await Promise.all(children.map((child) => new Promise((resolve) => {
    if (child.exitCode !== null) {
      resolve();
      return;
    }
    child.once("exit", resolve);
    setTimeout(resolve, 3000);
  })));
}

function browserCandidates() {
  const candidates = [];
  if (process.env.PLAYWRIGHT_EXECUTABLE_PATH) candidates.push(process.env.PLAYWRIGHT_EXECUTABLE_PATH);
  const cacheRoot = path.join(os.homedir(), ".cache", "ms-playwright");
  if (existsSync(cacheRoot)) {
    for (const name of readdirSync(cacheRoot).sort().reverse()) {
      if (!name.startsWith("chromium")) continue;
      candidates.push(path.join(cacheRoot, name, "chrome-linux64", "chrome"));
      candidates.push(path.join(cacheRoot, name, "chrome-headless-shell-linux64", "chrome-headless-shell"));
    }
  }
  candidates.push("/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome");
  return candidates;
}

export async function launchBrowser() {
  const options = { headless: true };
  for (const candidate of browserCandidates()) {
    try {
      await access(candidate, fsConstants.X_OK);
      options.executablePath = candidate;
      break;
    } catch {
      // Try the next installed browser.
    }
  }
  return chromium.launch(options);
}

export async function newAuditContext(browser, viewport, theme) {
  const context = await browser.newContext({
    viewport,
    deviceScaleFactor: 1,
    locale: "zh-CN",
    colorScheme: theme,
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  const events = { consoleErrors: [], pageErrors: [], fontRequests: [], fontResponses: [], fontFailures: [] };
  page.on("console", (message) => {
    if (message.type() === "error") events.consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => events.pageErrors.push(String(error)));
  page.on("request", (request) => {
    if (request.resourceType() === "font") events.fontRequests.push({ url: request.url(), method: request.method() });
  });
  page.on("response", (response) => {
    if (response.request().resourceType() === "font") {
      events.fontResponses.push({ url: response.url(), status: response.status(), contentType: response.headers()["content-type"] ?? "" });
    }
  });
  page.on("requestfailed", (request) => {
    if (request.resourceType() === "font") {
      events.fontFailures.push({ url: request.url(), error: request.failure()?.errorText ?? "request failed" });
    }
  });
  return { context, page, events };
}

export async function stabilizePage(page, theme) {
  await page.evaluate((selectedTheme) => {
    document.documentElement.lang = "zh-CN";
    document.documentElement.setAttribute("data-bs-navbar-position", "vertical");
    document.documentElement.setAttribute("data-bs-theme", selectedTheme);
  }, theme);
  await page.addStyleTag({
    content: "*, *::before, *::after { animation: none !important; transition: none !important; caret-color: transparent !important; }",
  });
  await page.evaluate(async () => {
    await document.fonts.ready;
    if (document.fonts.status !== "loaded") throw new Error("document.fonts did not reach loaded state");
  });
}

export async function openFixture(page, baseUrl, theme, reference, fixturePath = "/__ui/tabler-typography-fixture") {
  const target = reference ? baseUrl + "/layout-vertical.html" : baseUrl + fixturePath;
  await page.goto(target, { waitUntil: "networkidle" });
  if (reference) {
    await page.evaluate((html) => {
      // Set the fixture locale before its CJK text is first shaped. The
      // official Preview starts with lang=en, while StarMem starts zh-CN;
      // changing lang after shaping does not retroactively change fallback.
      document.documentElement.lang = "zh-CN";
      document.body.innerHTML = html;
    }, FIXTURE_MARKUP);
  }
  await stabilizePage(page, theme);
  if (reference) {
    // The Preview-only Astro toolbar is outside the copied Tabler fixture and
    // must not contaminate the fixture screenshot or its bounding box.
    await page.evaluate(() => {
      document.querySelectorAll("astro-dev-toolbar").forEach((element) => element.remove());
    });
  }
  await page.locator("#typography-fixture-root").waitFor();
}

export async function collectComputedStyles(page) {
  return page.evaluate(({ selectors, properties }) => Object.fromEntries(selectors.map((selector) => {
    const element = document.querySelector(selector);
    if (!element) return [selector, null];
    const style = getComputedStyle(element);
    return [selector, Object.fromEntries(properties.map((property) => [property, style[property]]))];
  })), { selectors: STYLE_SELECTORS, properties: STYLE_PROPERTIES });
}

export async function collectBoxes(page) {
  return page.evaluate((selectors) => Object.fromEntries(selectors.map((selector) => {
    const element = document.querySelector(selector);
    if (!element) return [selector, null];
    const rect = element.getBoundingClientRect();
    return [selector, { x: rect.x, y: rect.y, width: rect.width, height: rect.height }];
  })), BOX_SELECTORS);
}

export async function collectPlatformFonts(page, selectors) {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("DOM.enable");
  await cdp.send("CSS.enable");
  const result = {};
  for (const [name, selector] of Object.entries(selectors)) {
    const documentNode = await cdp.send("DOM.getDocument", { depth: -1 });
    const query = await cdp.send("DOM.querySelector", { nodeId: documentNode.root.nodeId, selector });
    if (!query.nodeId) {
      result[name] = null;
      continue;
    }
    result[name] = await cdp.send("CSS.getPlatformFontsForNode", { nodeId: query.nodeId });
  }
  await cdp.detach();
  return result;
}

export function normalize(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

export function fontFamilyTokens(value) {
  return normalize(value).split(",").map((token) => token.trim().replace(/^['\"]|['\"]$/g, "").toLowerCase()).filter(Boolean);
}

export function compareFontFamily(reference, actual) {
  const referenceTokens = fontFamilyTokens(reference);
  const actualTokens = fontFamilyTokens(actual);
  return {
    pass: normalize(reference) === normalize(actual),
    referenceTokens,
    actualTokens,
    extras: [],
  };
}

export async function pixelDiff(referencePath, starmemPath, diffPath) {
  const reference = PNG.sync.read(await readFile(referencePath));
  const starmem = PNG.sync.read(await readFile(starmemPath));
  if (reference.width !== starmem.width || reference.height !== starmem.height) {
    return { pass: false, diffPixels: null, diffRatio: 1, width: reference.width, height: reference.height, reason: "screenshot dimensions differ" };
  }
  const diff = new PNG({ width: reference.width, height: reference.height });
  const diffPixels = pixelmatch(reference.data, starmem.data, diff.data, reference.width, reference.height, { threshold: 0.1 });
  await mkdir(path.dirname(diffPath), { recursive: true });
  await writeFile(diffPath, PNG.sync.write(diff));
  const total = reference.width * reference.height;
  const diffRatio = total === 0 ? 0 : diffPixels / total;
  return {
    pass: diffRatio <= PIXEL_DIFF_MAX_RATIO,
    diffPixels,
    diffRatio,
    width: reference.width,
    height: reference.height,
    maxDiffRatio: PIXEL_DIFF_MAX_RATIO,
  };
}

export async function writeJson(filePath, value) {
  await mkdir(path.dirname(filePath), { recursive: true });
  await writeFile(filePath, JSON.stringify(value, null, 2) + "\n");
}

export function networkAndConsoleResult(events) {
  const badResponses = events.fontResponses.filter((item) => item.status < 200 || item.status >= 300);
  const badContentTypes = events.fontResponses.filter((item) => !/font|woff|opentype|truetype|octet-stream/i.test(item.contentType));
  return {
    pass: events.consoleErrors.length === 0 && events.pageErrors.length === 0 && events.fontFailures.length === 0 && badResponses.length === 0 && badContentTypes.length === 0,
    consoleErrors: events.consoleErrors,
    pageErrors: events.pageErrors,
    fontResponses: events.fontResponses,
    fontFailures: events.fontFailures,
    badFontResponses: badResponses,
    badFontContentTypes: badContentTypes,
    fontRequestDetails: events.fontRequests,
    fontRequests: events.fontRequests.length,
  };
}

export function flattenFamilies(platformFonts) {
  return Object.fromEntries(Object.entries(platformFonts).map(([name, value]) => [
    name,
    value?.fonts?.map((font) => ({ familyName: font.familyName, postScriptName: font.postScriptName, glyphCount: font.glyphCount })) ?? [],
  ]));
}
