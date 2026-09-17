// @ts-expect-error The file is an unmodified official Tabler build artifact.
import { Collapse, Dropdown, Modal, Offcanvas, Popover, Tab, Tooltip } from "../vendor/tabler/tabler.esm.js";

let scheduled = false;

export function initTabler(): void {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(() => {
    scheduled = false;
    document.querySelectorAll<HTMLElement>('[data-bs-toggle="dropdown"]').forEach((element) => Dropdown.getOrCreateInstance(element));
    document.querySelectorAll<HTMLElement>('[data-bs-toggle="collapse"]').forEach((element) => Collapse.getOrCreateInstance(element, { toggle: false }));
    document.querySelectorAll<HTMLElement>('[data-bs-toggle="offcanvas"]').forEach((element) => {
      const target = element.getAttribute("data-bs-target") ?? element.getAttribute("href");
      if (target?.startsWith("#")) {
        const panel = document.querySelector<HTMLElement>(target);
        if (panel) Offcanvas.getOrCreateInstance(panel);
      }
    });
    document.querySelectorAll<HTMLElement>('[data-bs-toggle="modal"]').forEach((element) => {
      const target = element.getAttribute("data-bs-target") ?? element.getAttribute("href");
      if (target?.startsWith("#")) {
        const modal = document.querySelector<HTMLElement>(target);
        if (modal) Modal.getOrCreateInstance(modal);
      }
    });
    document.querySelectorAll<HTMLElement>('[data-bs-toggle="tab"]').forEach((element) => Tab.getOrCreateInstance(element));
    document.querySelectorAll<HTMLElement>('[data-bs-toggle="tooltip"]').forEach((element) => Tooltip.getOrCreateInstance(element));
    document.querySelectorAll<HTMLElement>('[data-bs-toggle="popover"]').forEach((element) => Popover.getOrCreateInstance(element));
  });
}

export function applyStoredTheme(): void {
  const stored = localStorage.getItem("tabler-theme") ?? "auto";
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const dark = stored === "dark" || (stored === "auto" && prefersDark);
  document.documentElement.setAttribute("data-bs-theme", dark ? "dark" : "light");
}

export function setTheme(theme: "light" | "dark" | "auto"): void {
  localStorage.setItem("tabler-theme", theme);
  applyStoredTheme();
}

export function watchTheme(): void {
  document.documentElement.setAttribute("data-bs-navbar-position", "vertical");
  applyStoredTheme();
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if ((localStorage.getItem("tabler-theme") ?? "auto") === "auto") applyStoredTheme();
  });
}
