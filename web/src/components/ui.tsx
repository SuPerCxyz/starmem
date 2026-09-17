import { Children, isValidElement, type ReactNode } from "react";
import { Check, Clock3, ExternalLink, RotateCcw, X } from "./icons";

/** Tabler/Bootstrap components shared by every StarMem workspace. */
export const ui = {
  card: "card",
  surface: "card",
  chip: "badge bg-secondary-lt border-0",
  primaryButton: "btn btn-primary",
  secondaryButton: "btn btn-outline-secondary",
  input: "form-control",
  select: "form-select w-auto",
  textButton: "btn btn-link p-0",
  dangerTextButton: "btn btn-link p-0 text-danger",
  menuItem: "dropdown-item",
  sectionTitle: "card-title mb-0",
  sectionHint: "text-secondary",
  label: "form-label",
  divider: "border-top",
} as const;

const pageWidthClasses = {
  capture: "",
  browse: "",
  search: "",
  ai: "",
  detail: "",
  management: "",
} as const;

export function PageFrame({
  width,
  id,
  labelledBy,
  children,
  className = "",
}: {
  width: keyof typeof pageWidthClasses;
  id?: string;
  labelledBy?: string;
  children: ReactNode;
  className?: string;
}) {
  const pageChildren = Children.toArray(children);
  const headerIndex = pageChildren.findIndex((child) => isValidElement(child) && child.type === PageHeader);
  const header = headerIndex >= 0 ? pageChildren[headerIndex] : null;
  const bodyChildren = headerIndex >= 0 ? pageChildren.filter((_, index) => index !== headerIndex) : pageChildren;

  return (
    <div id={id} className={`page-wrapper ${pageWidthClasses[width]} ${className}`} aria-labelledby={labelledBy}>
      {header}
      <main className="page-body overflow-hidden">
        <div className="container-xl">{bodyChildren}</div>
      </main>
    </div>
  );
}

export function SectionHeader({
  title,
  description,
  actions,
  id,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  id?: string;
}) {
  return (
    <div className="row g-2 align-items-center">
      <div className="col">
        <h3 id={id} className={ui.sectionTitle}>{title}</h3>
        {description && <div className="text-secondary mt-1">{description}</div>}
      </div>
      {actions && <div className="col-auto ms-auto d-print-none">{actions}</div>}
    </div>
  );
}

export function LoadingState({ label = "正在载入…", rows = 3 }: { label?: string; rows?: number }) {
  return (
    <div className="placeholder-glow" role="status" aria-live="polite" aria-label={label}>
      <span className="visually-hidden">{label}</span>
      {Array.from({ length: rows }, (_, index) => (
        <div className="mb-3" key={index}>
          <span className={`placeholder col-${index % 2 === 0 ? "4" : "3"} placeholder-sm`} />
          <span className="placeholder col-9 placeholder-xs" />
          <span className="placeholder col-6 placeholder-xs" />
        </div>
      ))}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
  retryLabel = "重试",
}: {
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
}) {
  return (
    <div className="alert alert-danger" role="alert">
      <div>{message}</div>
      {onRetry && <button className="btn btn-outline-danger mt-3" type="button" onClick={onRetry}>{retryLabel}</button>}
    </div>
  );
}

export function DetailRail({ main, rail }: { main: ReactNode; rail: ReactNode }) {
  return (
    <div className="row row-cards">
      <div className="col-lg-8">{main}</div>
      <aside className="col-lg-4">{rail}</aside>
    </div>
  );
}

export type ManagementNavItem = { id: string; label: string; description?: string };

export function ManagementNav({
  items,
  active,
  onSelect,
}: {
  items: ManagementNavItem[];
  active: string;
  onSelect: (id: string) => void;
}) {
  return (
    <nav className="mb-3" aria-label="管理导航">
      <ul className="nav nav-tabs">
        {items.map((item) => (
          <li className="nav-item" key={item.id}>
            <button
              className={`nav-link${active === item.id ? " active" : ""}`}
              type="button"
              onClick={() => onSelect(item.id)}
              aria-current={active === item.id ? "page" : undefined}
              title={item.description}
            >
              {item.label}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export function PageHeader({
  id,
  title,
  description,
  actions,
}: {
  id?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="page-header d-print-none">
      <div className="container-xl">
        <div className="row g-2 align-items-center">
          <div className="col">
            <h2 id={id} className="page-title">{title}</h2>
            {description && <div className="text-secondary mt-1">{description}</div>}
          </div>
          {actions && <div className="col-auto ms-auto d-print-none">{actions}</div>}
        </div>
      </div>
    </header>
  );
}

export function FilterBar({
  children,
  count,
  countLabel = "条",
}: {
  children: ReactNode;
  count?: number;
  countLabel?: string;
}) {
  return (
    <div className="card mb-3">
      <div className="card-body py-2">
        <div className="d-flex flex-wrap align-items-center gap-2">
          {children}
          {count !== undefined && <span className="ms-auto text-secondary">共 {count} {countLabel}</span>}
        </div>
      </div>
    </div>
  );
}

export function EmptyState({
  id,
  title,
  description,
  actions,
  suggestions,
  icon,
  className = "",
}: {
  id?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  suggestions?: string[];
  icon?: ReactNode;
  className?: string;
}) {
  return (
    <div id={id} className={`empty empty-bordered ${className}`}>
      {icon && <div className="empty-icon">{icon}</div>}
      <p className="empty-title">{title}</p>
      {description && <p className="empty-subtitle text-secondary">{description}</p>}
      {suggestions && suggestions.length > 0 && (
        <ul className="list-unstyled text-secondary mb-3">
          {suggestions.map((item) => <li key={item}>· {item}</li>)}
        </ul>
      )}
      {actions && <div className="empty-action">{actions}</div>}
    </div>
  );
}

export type AIStatusKind = "processing" | "ready" | "review" | "failed";

const AI_STATUS: Record<AIStatusKind, { label: string; tone: string; Icon: typeof Check }> = {
  processing: { label: "处理中", tone: "status-blue", Icon: Clock3 },
  ready: { label: "已整理", tone: "status-green", Icon: Check },
  review: { label: "需复核", tone: "status-yellow", Icon: RotateCcw },
  failed: { label: "失败", tone: "status-red", Icon: X },
};

export function aiStatusKind(status: string): AIStatusKind {
  if (status === "pending" || status === "retrying") return "processing";
  if (status === "partial") return "review";
  if (status === "failed") return "failed";
  return "ready";
}

export function AIStatus({ status, onClick, className = "" }: { status: AIStatusKind; onClick?: () => void; className?: string }) {
  const { label, tone, Icon } = AI_STATUS[status];
  const content = <><span className={`status-dot${status === "processing" ? " status-dot-animated" : ""}`} /><Icon className="icon icon-sm" aria-hidden="true" /><span>{label}</span></>;
  if (!onClick) return <span className={`status ${tone} ${className}`}>{content}</span>;
  return <button type="button" className={`status ${tone} border-0 ${className}`} onClick={onClick}>{content}</button>;
}

export type SourceItemData = { title: string; meta?: string[]; snippet: string; index?: number; href?: string; hrefLabel?: string };

export function SourceItem({ source, onOpenEntry }: { source: SourceItemData; onOpenEntry?: () => void }) {
  return (
    <article className="list-group-item px-0">
      <div className="d-flex flex-wrap align-items-center gap-2">
        {source.index !== undefined && <span className="badge bg-secondary-lt">来源 {source.index}</span>}
        <strong>{source.title}</strong>
        {source.meta?.filter(Boolean).map((item) => <span className="text-secondary" key={item}>{item}</span>)}
      </div>
      <p className="mb-2 mt-2">{source.snippet}</p>
      <div className="d-flex flex-wrap align-items-center gap-3">
        {source.href && <a className={ui.textButton} href={source.href} target="_blank" rel="noreferrer">{source.hrefLabel ?? "原 URL"}</a>}
        {onOpenEntry && <button className={ui.secondaryButton} type="button" onClick={onOpenEntry}><ExternalLink className="icon icon-sm" aria-hidden="true" />跳到原文</button>}
      </div>
    </article>
  );
}
