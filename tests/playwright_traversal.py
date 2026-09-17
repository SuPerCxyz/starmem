"""Full-function traversal over each page's key controls.

Run against a running Compose Web service:
    STARMEM_TEST_EMAIL=... STARMEM_TEST_PASSWORD=... python3 tests/playwright_traversal.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import date
from uuid import uuid4

from playwright.sync_api import Page, sync_playwright

BASE = "http://localhost:18780"
ENTRY_STATUS = re.compile(r"^(处理中|已整理|需复核|失败)$")


def _login(page: Page, email: str, password: str) -> None:
    page.goto(BASE + "/")
    page.wait_for_load_state("networkidle")
    if page.get_by_role("heading", name="欢迎回到 StarMem").is_visible():
        page.get_by_label("邮箱").fill(email)
        page.get_by_label("密码").fill(password)
        page.get_by_role("button", name="登录 StarMem").click()
    page.get_by_label("记录内容").wait_for()


def _open_page(page: Page, label: str) -> None:
    if page.viewport_size["width"] <= 768 and not page.locator("#sidebar-menu.show").is_visible():
        page.locator("button.navbar-toggler:visible").first.click()
    page.locator("#sidebar-menu").get_by_role("button", name=label, exact=True).click()


def _csrf(page: Page) -> str:
    value = page.evaluate(
        "() => { const part = document.cookie.split('; ').find((item) => item.startsWith('starmem_csrf=')); return part ? decodeURIComponent(part.split('=')[1]) : ''; }"
    )
    assert value, "CSRF cookie missing"
    return value


def _api(page: Page, method: str, path: str, body: dict | None = None) -> dict:
    csrf = _csrf(page)
    return page.evaluate(
        """async ({ method, path, body, csrf }) => {
            const response = await fetch(`/api/v1${path}`, {
                method,
                credentials: 'include',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
                body: body ? JSON.stringify(body) : undefined,
            });
            if (response.status === 204) return { status: response.status };
            const payload = await response.json().catch(() => ({}));
            return { status: response.status, payload };
        }""",
        {"method": method, "path": path, "body": body, "csrf": csrf},
    )


def _delete_prompt_versions(version_ids: list[str]) -> None:
    if not version_ids:
        return
    script = (
        "from app.db import SessionLocal; from sqlalchemy import delete; "
        "from app.models import PromptVersion; import sys; "
        "ids = sys.argv[1:]; "
        "s = SessionLocal(); s.execute(delete(PromptVersion).where(PromptVersion.id.in_(ids))); s.commit()"
    )
    subprocess.run(
        ["docker", "compose", "exec", "-T", "api", "python", "-c", script, *version_ids],
        check=True,
    )


def main() -> int:
    email = os.environ["STARMEM_TEST_EMAIL"]
    password = os.environ["STARMEM_TEST_PASSWORD"]
    marker = f"traversal-{uuid4()}"
    console_errors: list[str] = []
    page_errors: list[str] = []
    created_versions: list[str] = []
    saved_search_id: str | None = None
    memory_id: str | None = None
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 375, "height": 812}, reduced_motion="reduce")
        page = context.new_page()
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.on("dialog", lambda dialog: dialog.accept())
        _login(page, email, password)
        console_errors.clear()
        page_errors.clear()

        # --- Capture: keyboard save, empty guard ---
        capture = page.get_by_label("记录内容")
        capture.fill("")
        capture.press("Control+Enter")
        page.get_by_text("内容为空，无法保存。").wait_for()
        capture.fill(f"{marker}\n\n```yaml\nservice: starmem\n```")
        capture.press("Control+Enter")
        page.get_by_text(marker).first.wait_for()

        # --- Entry card: fallback type chips, metadata multi-class, AI steps, related ---
        card = page.locator(".entry-card").filter(has_text=marker).first
        card.wait_for()
        entry_id = (card.get_attribute("id") or "").removeprefix("entry-")
        assert entry_id, "entry id missing"
        card.locator(".entry-ai-steps").wait_for()
        card.get_by_role("button", name=ENTRY_STATUS).first.click()
        detail = page.get_by_role("dialog").filter(has_text="处理进度")
        detail.wait_for()
        detail.get_by_text("相关记录", exact=True).wait_for()
        detail.get_by_label("Metadata 类型").fill("log, decision")
        detail.get_by_role("button", name="保存 Metadata").click()
        detail.get_by_text("Metadata 已保存").wait_for()
        detail.get_by_role("button", name="关闭", exact=True).click()
        card.locator(".entry-meta", has_text="decision").wait_for()

        # --- Timeline: custom date range narrows the result set ---
        today = date.today().isoformat()
        _open_page(page, "时间线")
        page.get_by_label("起始日期", exact=True).first.wait_for()
        page.get_by_label("起始日期", exact=True).first.fill(today)
        page.get_by_label("结束日期", exact=True).first.fill(today)
        page.locator(".entry-card").filter(has_text=marker).first.wait_for()
        page.get_by_label("起始日期", exact=True).first.fill("2099-01-01")
        page.get_by_text("没有匹配的记录").wait_for()
        page.reload()
        page.get_by_label("起始日期", exact=True).first.wait_for()
        page.locator(".entry-card").filter(has_text=marker).first.wait_for()

        # --- Search: mode + filters + saved search round-trip ---
        _open_page(page, "搜索")
        page.get_by_label("检索模式").select_option("fulltext")
        page.get_by_label("搜索记录").fill(marker)
        page.locator(".scope-form button.btn-primary").click()
        page.get_by_role("button", name="查看原文").first.wait_for()
        page.locator(".search-filters summary").click()
        page.get_by_label("内容类型过滤").fill("decision")
        page.locator(".scope-form button.btn-primary").click()
        page.get_by_role("button", name="查看原文").first.wait_for()
        page.get_by_label("保存搜索名称").fill(f"Traversal {marker}")
        page.get_by_role("button", name="保存搜索").click()
        _open_page(page, "时间线")
        _open_page(page, "搜索")
        row = page.locator(".saved-search-row", has_text=f"Traversal {marker}")
        row.wait_for()
        saved_search_id = page.evaluate(
            """async (name) => {
                const response = await fetch('/api/v1/saved-searches', { credentials: 'include' });
                const items = await response.json();
                const found = items.find((item) => item.name === name);
                return found ? found.id : null;
            }""",
            f"Traversal {marker}",
        )
        page.locator(".search-filters summary").click()
        page.get_by_label("内容类型过滤").fill("")
        row.get_by_role("button").first.click()
        page.get_by_role("button", name="查看原文").first.wait_for()
        assert page.get_by_label("内容类型过滤").input_value() == "decision"
        if saved_search_id:
            _api(page, "DELETE", f"/saved-searches/{saved_search_id}")
        saved_search_id = None

        # --- More: memory lifecycle seeded through the API ---
        seeded = _api(
            page,
            "POST",
            f"/entries/{entry_id}/memory-candidates",
            {
                "subject": f"svc-{marker}",
                "predicate": "runs_on",
                "value": f"host-{marker}",
                "memory_text": f"{marker} runs on host",
            },
        )
        assert seeded["status"] == 201, seeded
        memory_id = seeded["payload"]["memory"]["id"]

        _open_page(page, "设置")
        page.get_by_role("button", name="Memory", exact=True).click()
        page.get_by_text("Memory 生命周期").wait_for()
        page.get_by_label("Memory 状态筛选").select_option("active")
        memory_row = page.locator(".memory-row").filter(has_text=marker)
        memory_row.wait_for()
        memory_row.get_by_role("button", name="标记过期").click()
        page.get_by_label("Memory 状态筛选").select_option("expired")
        page.locator(".memory-row").filter(has_text=marker).wait_for()
        page.locator(".memory-row").filter(has_text=marker).get_by_role("button", name="确认").click()
        page.get_by_label("Memory 状态筛选").select_option("active")
        page.locator(".memory-row").filter(has_text=marker).wait_for()
        page.locator(".memory-row").filter(has_text=marker).get_by_role("button", name="删除").click()
        page.get_by_label("Memory 状态筛选").select_option("deleted")
        page.locator(".memory-row").filter(has_text=marker).wait_for()

        # --- Prompt Studio: clone, draft params, preview, test cases, draft test ---
        page.get_by_role("button", name="Prompt Studio", exact=True).click()
        page.locator(".prompt-studio-card select").select_option("classification")
        with page.expect_response(lambda response: "/clone" in response.url) as clone_info:
            page.get_by_role("button", name="克隆内置").click()
        page.get_by_text("已克隆内置 Prompt").wait_for()
        clone_payload = clone_info.value.json()
        if clone_payload.get("id"):
            created_versions.append(clone_payload["id"])
        page.get_by_label("Task Prompt").fill(f"Traversal task prompt {marker}")
        page.get_by_label("Prompt Temperature").fill("0.2")
        with page.expect_response(lambda response: "/draft" in response.url) as draft_info:
            page.get_by_role("button", name="保存 Draft").click()
        page.get_by_text("已保存 Draft").wait_for()
        draft_payload = draft_info.value.json()
        if draft_payload.get("id"):
            created_versions.append(draft_payload["id"])
        page.get_by_role("tab", name="测试用例").click()
        page.get_by_label("Test Case 名称").fill(f"case-{marker}")
        page.get_by_label("Test Case 输入 JSON").fill('{"raw_content": "hello"}')
        page.get_by_role("button", name="新增 Test Case").click()
        case_row = page.locator(".test-case-editor .similar-row").filter(has_text=f"case-{marker}")
        case_row.wait_for()
        case_row.get_by_role("button", name="删除").click()
        page.get_by_text("暂无 Test Case。").wait_for()
        page.get_by_role("tab", name="编辑").click()
        page.locator(".prompt-preview summary").click()
        page.locator(".prompt-preview pre").wait_for()

        # --- Cleanup ---
        if saved_search_id:
            _api(page, "DELETE", f"/saved-searches/{saved_search_id}")
        if memory_id:
            _api(page, "DELETE", f"/memories/{memory_id}")
        removed = _api(page, "DELETE", f"/entries/{entry_id}")
        assert removed["status"] == 204, removed
        page.goto(BASE + "/capture")
        page.get_by_label("记录内容").wait_for()
        assert page.get_by_text(marker).count() == 0

        assert not console_errors, console_errors
        assert not page_errors, page_errors
        page.screenshot(path="/tmp/starmem-playwright-traversal.png", full_page=True)
        browser.close()
    _delete_prompt_versions(created_versions)
    print("playwright-traversal: passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
