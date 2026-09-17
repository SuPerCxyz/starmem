"""Composition QA for the route/page-level StarMem UI contract.

Run against a running Compose Web service with STARMEM_TEST_EMAIL and
STARMEM_TEST_PASSWORD set to the runtime admin credentials.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import Page, sync_playwright

BASE = "http://localhost:18780"
VIEWPORTS = (390, 430, 768, 1024, 1440, 1920)


def _env(name: str) -> str:
    prefix = name + "="
    for line in Path(".env").read_text().splitlines():
        if line.startswith(prefix):
            value = line[len(prefix) :].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                return value[1:-1]
            return value
    return ""


def _login(page: Page) -> None:
    page.goto(BASE + "/capture")
    page.wait_for_load_state("networkidle")
    if page.get_by_role("heading", name="欢迎回到 StarMem").is_visible():
        page.get_by_label("邮箱").fill(_env("STARMEM_ADMIN_EMAIL") or "admin@starmem.local")
        page.get_by_label("密码").fill(_env("STARMEM_ADMIN_PASSWORD"))
        page.get_by_role("button", name="登录 StarMem").click()
    page.get_by_label("记录内容").wait_for(timeout=30000)


def _api(page: Page, path: str):
    return page.evaluate(
        """async (path) => {
          const response = await fetch('/api/v1' + path, {credentials: 'include'});
          return response.ok ? await response.json() : null;
        }""",
        path,
    )


def _check_route(page: Page, path: str, heading: str) -> None:
    page.goto(BASE + path)
    page.wait_for_load_state("networkidle")
    page.get_by_role("heading", name=heading, exact=True).first.wait_for(timeout=30000)
    assert page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth") == 0, path


def main() -> int:
    if not _env("STARMEM_ADMIN_PASSWORD"):
        raise SystemExit("runtime admin password is not configured in .env")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        page = context.new_page()
        console_errors: list[str] = []
        page_errors: list[str] = []
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        _login(page)
        console_errors.clear()
        page_errors.clear()

        entries = _api(page, "/entries") or {}
        jobs = _api(page, "/ai-jobs") or []
        memories = _api(page, "/memories?status=all") or []
        projects = _api(page, "/projects") or []
        topics = _api(page, "/topics") or []
        entities = _api(page, "/entities") or []
        prompts = _api(page, "/prompts") or []

        routes = [
            ("/", "有什么需要记住的？"),
            ("/capture", "有什么需要记住的？"),
            ("/timeline", "时间线"),
            ("/search", "搜索任何记忆"),
            ("/ask", "问记忆"),
            ("/ask/sources", "问记忆"),
            ("/inbox", "所有输入都在这里处理"),
            ("/settings", "设置与操作"),
            ("/settings/models", "模型与 Provider"),
            ("/settings/prompts", "Prompt Studio"),
            ("/settings/jobs", "AI 任务"),
            ("/settings/memory", "Memory"),
            ("/settings/backup", "数据搬迁"),
            ("/sources", "来源"),
            ("/workbench", "知识工作台"),
            ("/missing-route", "页面不存在"),
        ]
        if prompts:
            name = quote(prompts[0]["name"], safe="")
            routes.extend(
                [
                    (f"/settings/prompts/{name}/versions", "Prompt Studio"),
                    (f"/settings/prompts/{name}/tests", "Prompt Studio"),
                ]
            )
        if entries.get("items"):
            entry_id = entries["items"][0]["id"]
            routes.extend(
                [
                    (f"/entries/{entry_id}", "Entry 详情"),
                    (f"/entries/{entry_id}/history", "Entry 版本历史"),
                ]
            )
        if jobs:
            routes.append((f"/settings/jobs/{jobs[0]['id']}", jobs[0]["job_type"]))
        if memories:
            routes.append((f"/settings/memory/{memories[0]['id']}", "Memory 详情"))
        for kind, items in (("project", projects), ("topic", topics), ("entity", entities)):
            if items:
                routes.append((f"/workbench/{kind}/{items[0]['id']}", "知识工作台"))

        for path, heading in routes:
            _check_route(page, path, heading)

        for width in VIEWPORTS:
            page.set_viewport_size({"width": width, "height": 900})
            _check_route(page, "/capture", "有什么需要记住的？")
            if width <= 430:
                assert page.locator("button.navbar-toggler:visible").count() == 1

        dark_context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        dark_page = dark_context.new_page()
        dark_errors: list[str] = []
        dark_page.on("console", lambda message: dark_errors.append(message.text) if message.type == "error" else None)
        dark_page.on("pageerror", lambda error: dark_errors.append(str(error)))
        _login(dark_page)
        dark_errors.clear()
        dark_page.evaluate("localStorage.setItem('tabler-theme', 'dark'); document.documentElement.setAttribute('data-bs-theme', 'dark')")
        for path, heading in routes:
            _check_route(dark_page, path, heading)
            assert dark_page.locator('html[data-bs-theme="dark"]').count() == 1

        assert not console_errors, console_errors
        assert not page_errors, page_errors
        assert not dark_errors, dark_errors
        dark_context.close()
        browser.close()
    print(f"playwright-composition: passed ({len(routes)} routes; {len(VIEWPORTS)} viewports; dark mode)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
