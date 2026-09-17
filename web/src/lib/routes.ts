export type ShellPage = "capture" | "timeline" | "search" | "ask" | "more" | "inbox" | "workbench" | "jobs" | "sources";
export type WorkbenchKind = "project" | "topic" | "entity";
export type ManagementSection = "overview" | "models" | "prompts" | "jobs" | "memory" | "backup";
export type PromptView = "editor" | "versions" | "tests";

export type WorkspaceRoute = {
  page: ShellPage | "entry" | "entry-history" | "job-detail" | "memory-detail" | "not-found";
  id?: string;
  workbenchKind?: WorkbenchKind;
  workbenchId?: string;
  managementSection?: ManagementSection;
  promptName?: string;
  promptView?: PromptView;
};

const shellPaths: Record<ShellPage, string> = {
  capture: "/capture",
  timeline: "/timeline",
  search: "/search",
  ask: "/ask",
  more: "/settings",
  inbox: "/inbox",
  workbench: "/workbench",
  jobs: "/settings/jobs",
  sources: "/sources",
};

function normalize(pathname: string): string {
  const path = pathname.replace(/\/+$/, "");
  return path || "/";
}

function decodeSegment(value: string): string | null {
  try {
    return decodeURIComponent(value);
  } catch {
    return null;
  }
}

export function parseRoute(pathname: string): WorkspaceRoute {
  const path = normalize(pathname);
  if (path === "/" || path === "/capture") return { page: "capture" };
  if (path === "/timeline") return { page: "timeline" };
  if (path === "/search") return { page: "search" };
  if (path === "/ask") return { page: "ask" };
  if (path === "/ask/sources") return { page: "ask" };
  if (path === "/inbox") return { page: "inbox" };
  if (path === "/workbench") return { page: "workbench" };
  if (path === "/sources") return { page: "sources" };
  if (path === "/settings") return { page: "more", managementSection: "overview" };
  if (path === "/settings/models") return { page: "more", managementSection: "models" };
  if (path === "/settings/prompts") return { page: "more", managementSection: "prompts", promptView: "editor" };
  if (path === "/settings/jobs") return { page: "jobs", managementSection: "jobs" };
  if (path === "/settings/memory") return { page: "more", managementSection: "memory" };
  if (path === "/settings/backup") return { page: "more", managementSection: "backup" };

  const promptMatch = path.match(/^\/settings\/prompts\/([^/]+)\/(versions|tests)$/);
  if (promptMatch) {
    const promptName = decodeSegment(promptMatch[1]);
    if (promptName) return { page: "more", managementSection: "prompts", promptName, promptView: promptMatch[2] === "versions" ? "versions" : "tests" };
  }

  const jobMatch = path.match(/^\/settings\/jobs\/([^/]+)$/);
  if (jobMatch) {
    const id = decodeSegment(jobMatch[1]);
    if (id) return { page: "job-detail", id };
  }

  const memoryMatch = path.match(/^\/settings\/memory\/([^/]+)$/);
  if (memoryMatch) {
    const id = decodeSegment(memoryMatch[1]);
    if (id) return { page: "memory-detail", id };
  }

  const workbenchMatch = path.match(/^\/workbench\/(project|topic|entity)\/([^/]+)$/);
  if (workbenchMatch) {
    const workbenchId = decodeSegment(workbenchMatch[2]);
    if (workbenchId) return { page: "workbench", workbenchKind: workbenchMatch[1] as WorkbenchKind, workbenchId };
  }

  const entryMatch = path.match(/^\/entries\/([^/]+)(\/history)?$/);
  if (entryMatch) {
    const id = decodeSegment(entryMatch[1]);
    if (id) return { page: entryMatch[2] ? "entry-history" : "entry", id };
  }

  return { page: "not-found" };
}

export function pathForRoute(route: WorkspaceRoute): string {
  if (route.page in shellPaths && route.page !== "more" && !route.workbenchId) return shellPaths[route.page as ShellPage];
  if (route.page === "entry" && route.id) return `/entries/${encodeURIComponent(route.id)}`;
  if (route.page === "entry-history" && route.id) return `/entries/${encodeURIComponent(route.id)}/history`;
  if (route.page === "job-detail" && route.id) return `/settings/jobs/${encodeURIComponent(route.id)}`;
  if (route.page === "memory-detail" && route.id) return `/settings/memory/${encodeURIComponent(route.id)}`;
  if (route.page === "workbench" && route.workbenchKind && route.workbenchId) return `/workbench/${route.workbenchKind}/${encodeURIComponent(route.workbenchId)}`;
  if (route.page === "more") {
    if (route.managementSection === "models") return "/settings/models";
    if (route.managementSection === "prompts") {
      if (route.promptName && route.promptView === "versions") return `/settings/prompts/${encodeURIComponent(route.promptName)}/versions`;
      if (route.promptName && route.promptView === "tests") return `/settings/prompts/${encodeURIComponent(route.promptName)}/tests`;
      return "/settings/prompts";
    }
    if (route.managementSection === "memory") return "/settings/memory";
    if (route.managementSection === "backup") return "/settings/backup";
    return "/settings";
  }
  return "/404";
}

export function activeShellPage(route: WorkspaceRoute): ShellPage {
  if (route.page === "entry" || route.page === "entry-history") return "timeline";
  if (route.page === "job-detail" || route.page === "memory-detail") return "more";
  if (route.page === "not-found") return "capture";
  if (route.page === "more" && route.managementSection === "jobs") return "jobs";
  return route.page as ShellPage;
}

export function navigateTo(route: WorkspaceRoute, replace = false): void {
  const path = pathForRoute(route);
  window.history[replace ? "replaceState" : "pushState"]({}, "", path);
}
