import { useEffect, type ReactNode } from "react";
import { Archive, Clock3, FileText, Inbox, Link2, LogOut, Menu, Search, Settings, Sparkles, Check } from "./icons";
import type { ShellPage } from "../lib/routes";
import { initTabler } from "../theme/tabler";

type SidebarItem = { page: ShellPage; label: string; icon: typeof FileText };

const sidebarGroups: Array<{ label: string; items: SidebarItem[] }> = [
  {
    label: "工作区",
    items: [
      { page: "capture", label: "记录", icon: FileText },
      { page: "timeline", label: "时间线", icon: Clock3 },
      { page: "search", label: "搜索", icon: Search },
      { page: "ask", label: "问记忆", icon: Sparkles },
    ],
  },
  {
    label: "知识",
    items: [
      { page: "workbench", label: "知识工作台", icon: Archive },
      { page: "sources", label: "来源", icon: Link2 },
    ],
  },
  {
    label: "系统",
    items: [
      { page: "inbox", label: "Import Inbox", icon: Inbox },
      { page: "jobs", label: "AI 任务", icon: Check },
      { page: "more", label: "设置", icon: Settings },
    ],
  },
];

const pageLabels: Record<ShellPage, string> = {
  capture: "记录",
  timeline: "时间线",
  search: "搜索",
  ask: "问记忆",
  more: "设置",
  inbox: "Import Inbox",
  workbench: "知识工作台",
  jobs: "AI 任务",
  sources: "来源",
};

function SidebarGroup({ label, items, page, onNavigate }: { label: string; items: SidebarItem[]; page: ShellPage; onNavigate: (page: ShellPage) => void }) {
  return (
    <>
      <li className="nav-section-title">{label}</li>
      {items.map(({ page: target, label: itemLabel, icon: Icon }) => (
        <li className={`nav-item${page === target ? " active" : ""}`} key={target}>
          <button className="nav-link" type="button" onClick={() => onNavigate(target)} aria-current={page === target ? "page" : undefined}>
            <span className="nav-link-icon"><Icon className="icon" aria-hidden="true" /></span>
            <span className="nav-link-title">{itemLabel}</span>
          </button>
        </li>
      ))}
    </>
  );
}

export function AppShell({ page, onNavigate, onLogout, children }: { page: ShellPage; onNavigate: (page: ShellPage) => void; onLogout: () => void; children: ReactNode }) {
  useEffect(() => {
    initTabler();
  }, [page]);

  return (
    <div className="page">
      <aside className="navbar navbar-vertical navbar-expand-lg">
        <div className="container-fluid">
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#sidebar-menu" aria-controls="sidebar-menu" aria-expanded="false" aria-label="打开导航">
            <span className="navbar-toggler-icon" />
          </button>
          <div className="navbar-brand navbar-brand-autodark">
            <a href="/" aria-label="StarMem" className="d-flex align-items-center gap-2">
              <img src="/starmem-logo.png" width="32" height="32" alt="" className="navbar-brand-image" aria-hidden="true" />
              <span className="d-none d-lg-inline">StarMem</span>
            </a>
          </div>
          <nav className="collapse navbar-collapse" id="sidebar-menu" aria-label="主导航">
            <ul className="navbar-nav pt-lg-3">
              {sidebarGroups.map((group) => <SidebarGroup key={group.label} {...group} page={page} onNavigate={onNavigate} />)}
            </ul>
          </nav>
          <div className="navbar-footer">
            <ul className="navbar-nav">
              <li className="nav-item">
                <button className="nav-link" type="button" onClick={onLogout}>
                  <span className="nav-link-icon"><LogOut className="icon" aria-hidden="true" /></span>
                  <span className="nav-link-title">退出登录</span>
                </button>
              </li>
            </ul>
          </div>
        </div>
      </aside>

      <header className="navbar navbar-expand-sm d-print-none">
        <div className="container-xl">
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#sidebar-menu" aria-controls="sidebar-menu" aria-expanded="false" aria-label="打开导航">
            <span className="navbar-toggler-icon" />
          </button>
          <div className="navbar-brand navbar-brand-autodark d-md-none">
            <a href="/" className="d-flex align-items-center gap-2">
              <img src="/starmem-logo.png" width="32" height="32" alt="" className="navbar-brand-image" aria-hidden="true" />
              <span>StarMem</span>
            </a>
          </div>
          <div className="navbar-nav flex-row order-md-last ms-auto">
            <span className="nav-link text-secondary">{pageLabels[page]}</span>
          </div>
        </div>
      </header>

      {children}
    </div>
  );
}
