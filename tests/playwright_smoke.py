"""Run with STARMEM_TEST_EMAIL/ STARMEM_TEST_PASSWORD against a running Compose Web service.

选择器基于 Tabler 迁移后的 UI：
- 视觉类全部来自 Tabler/Bootstrap 官方 class，测试主要依赖可访问性名称
  （label / role / aria-label）与语义化锚点（id、aria-labelledby、section）。
"""

from __future__ import annotations

import os
import re
import sys
import json
from uuid import uuid4

from playwright.sync_api import Page, sync_playwright

VIEW_SOURCES = re.compile(r"^查看\s*\d+\s*条来源$")
ENTRY_STATUS = re.compile(r"^(处理中|已整理|需复核|失败)$")


def _login(page: Page, email: str, password: str) -> None:
    page.goto("http://localhost:18780/")
    page.wait_for_load_state("networkidle")
    if page.get_by_role("heading", name="欢迎回到 StarMem").is_visible():
        page.get_by_label("邮箱").fill(email)
        page.get_by_label("密码").fill(password)
        page.get_by_role("button", name="登录 StarMem").click()
    page.get_by_label("记录内容").wait_for()


def _mobile_nav(page: Page):
    if page.viewport_size["width"] <= 768 and not page.locator("#sidebar-menu.show").is_visible():
        page.locator("button.navbar-toggler:visible").first.click()
    return page.locator("#sidebar-menu")


def _entry_cards(page: Page):
    return page.locator("article[id^=entry-]")


def _entry_body(card):
    """EntryCard 正文按钮带 aria-expanded 且不是 menu 触发器。"""
    return card.locator("button[aria-expanded]:not([aria-haspopup])").first


def main() -> int:
    email = os.environ["STARMEM_TEST_EMAIL"]
    password = os.environ["STARMEM_TEST_PASSWORD"]
    marker = f"playwright-smoke-{uuid4()}"
    console_errors: list[str] = []
    page_errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 375, "height": 812}, reduced_motion="reduce"
        )
        page = context.new_page()
        page.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        _login(page, email, password)
        console_errors.clear()
        page_errors.clear()

        manifest = page.request.get("http://localhost:18780/manifest.webmanifest")
        assert manifest.ok and manifest.json()["display"] == "standalone"
        share_target = manifest.json()["share_target"]
        assert share_target["action"] == "/share"
        assert share_target["method"] == "POST"
        assert (
            page.locator("link[rel='manifest']").get_attribute("href")
            == "/manifest.webmanifest"
        )

        page.wait_for_timeout(500)
        if not page.evaluate("navigator.serviceWorker.controller !== null"):
            page.reload()
        page.wait_for_function("navigator.serviceWorker.controller !== null")
        shared_text = f"shared-text-{uuid4()}"
        share_response = page.evaluate(
            """async (text) => {
                await navigator.serviceWorker.ready;
                const body = new FormData();
                body.append('title', 'Shared title');
                body.append('text', text);
                body.append('url', 'https://example.com/shared');
                const response = await fetch('/share', { method: 'POST', body });
                return { status: response.status, url: response.url };
            }""",
            shared_text,
        )
        assert share_response["status"] == 200
        assert "shared=1" in share_response["url"]
        page.goto("http://localhost:18780/?shared=1")
        page.get_by_label("记录内容").wait_for()
        assert page.get_by_label("记录内容").input_value() == shared_text
        page.get_by_label("添加内容").click()
        page.get_by_role("button", name="改用分享的网页").click()
        assert (
            page.get_by_label("网页地址").input_value() == "https://example.com/shared"
        )
        page.get_by_role("button", name="返回文字").click()

        shared_file = f"shared-file-{uuid4()}.txt"
        page.evaluate(
            """async (filename) => {
                await navigator.serviceWorker.ready;
                const body = new FormData();
                body.append('files', new Blob(['shared file payload'], { type: 'text/plain' }), filename);
                const response = await fetch('/share', { method: 'POST', body });
                if (response.status !== 200 || !response.url.includes('shared=1')) throw new Error(`share status ${response.status}`);
            }""",
            shared_file,
        )
        page.goto("http://localhost:18780/?shared=1")
        page.get_by_label("选择文件").wait_for()
        page.get_by_text(shared_file).last.wait_for()

        for width in (375, 768, 1024, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            page.wait_for_timeout(100)
            assert page.evaluate("document.documentElement.scrollWidth") == width, f"horizontal overflow at {width}: {page.evaluate('document.documentElement.scrollWidth')}"
            if width == 375:
                assert page.locator("button.navbar-toggler:visible").count() == 1
            else:
                assert page.locator("aside.navbar-vertical").is_visible()

        page.set_viewport_size({"width": 375, "height": 812})
        page.get_by_role("button", name="返回文字").click()
        page.get_by_label("记录内容").fill(
            f"{marker}\n\n```yaml\nservice: starmem\n```"
        )
        page.get_by_label("保存记录").click()
        page.get_by_text(marker).wait_for()

        _mobile_nav(page).get_by_role("button", name="搜索", exact=True).click()
        search_form = page.locator("form").filter(has=page.get_by_label("搜索记录"))
        page.get_by_label("搜索记录").fill(marker)
        search_form.locator("button").last.click()
        page.get_by_label("保存搜索名称").fill(f"Saved {marker}")
        page.get_by_role("button", name="保存搜索").click()
        # 保存的搜索展示在「未搜索态」，切页以重置搜索结果
        _mobile_nav(page).get_by_role("button", name="时间线", exact=True).click()
        page.wait_for_timeout(1000)
        _mobile_nav(page).get_by_role("button", name="搜索", exact=True).click()
        page.wait_for_timeout(1800)
        saved_section = page.locator("section[aria-labelledby=saved-searches-heading]")
        saved_section.get_by_text(f"Saved {marker}").wait_for()
        saved_section.get_by_role("button", name=f"Saved {marker}").locator(
            "xpath=.."
        ).get_by_role("button", name="删除").click()
        page.get_by_text(f"Saved {marker}").wait_for(state="detached")
        # 重新搜索以获得结果卡片
        page.get_by_label("搜索记录").fill(marker)
        page.locator("form").filter(has=page.get_by_label("搜索记录")).locator(
            "button"
        ).last.click()
        page.wait_for_timeout(2500)
        page.get_by_role("button", name="查看原文").first.click()
        _entry_cards(page).filter(has_text=marker).wait_for()

        _mobile_nav(page).get_by_role("button", name="问记忆", exact=True).click()
        ask_form = page.locator("form").filter(has=page.get_by_label("问题"))
        page.get_by_label("问题").fill(f"记录 {marker} 是什么？")
        ask_form.locator("button").last.click()
        page.get_by_role("button", name=VIEW_SOURCES).wait_for()

        _mobile_nav(page).get_by_role("button", name="记录", exact=True).click()
        target_card = _entry_cards(page).filter(has_text=marker)
        target_card.wait_for()
        target_card.get_by_role("button", name=ENTRY_STATUS).first.click()
        detail = page.get_by_role("dialog").filter(has_text="处理进度")
        detail.wait_for()
        detail.get_by_text("本地安全扫描").wait_for()
        detail.get_by_label("Metadata Importance").fill("42")
        detail.get_by_role("button", name="保存 Metadata").click()
        detail.get_by_text("Metadata 已保存").wait_for()
        detail.get_by_role("button", name="关闭", exact=True).click()

        _mobile_nav(page).get_by_role("button", name="设置", exact=True).click()
        page.get_by_role("button", name="Prompt Studio", exact=True).click()
        page.locator("#more-heading").wait_for()
        page.get_by_role("button", name="数据搬迁", exact=True).click()
        page.locator("#more-heading").filter(has_text="数据搬迁").wait_for()
        with page.expect_download() as download_info:
            page.get_by_role("link", name="导出 JSON", exact=True).click()
        assert download_info.value.suggested_filename == "starmem-export.json"
        native_backup = json.dumps(
            {
                "format": "starmem.native.v1",
                "entries": [
                    {"raw_content": f"{marker}\n\n```yaml\nservice: starmem\n```"}
                ],
            }
        )
        page.get_by_label("选择原生备份文件").set_input_files(
            {
                "name": "starmem-smoke.json",
                "mimeType": "application/json",
                "buffer": native_backup.encode(),
            }
        )
        page.get_by_text("已导入 0 条，跳过 1 条。").wait_for()
        _mobile_nav(page).get_by_role("button", name="设置", exact=True).click()
        page.get_by_role("button", name="概览", exact=True).click()
        page.get_by_role("button", name="打开知识工作台").click()
        page.get_by_role("heading", name="知识工作台").wait_for()
        page.get_by_role("tab", name="主题").click()
        page.get_by_role("heading", name="Smart Views").wait_for()
        smart_section = page.locator("section[aria-labelledby=smart-view-heading]")
        smart_section.locator("button", has_text="最近常问").click()
        smart_section.get_by_text(marker).first.wait_for()

        _mobile_nav(page).get_by_role("button", name="记录", exact=True).click()
        page.wait_for_timeout(800)
        # 分享载荷仍驻留在 Workspace 时，Capture 重新挂载会回到文件模式
        if page.get_by_role("button", name="返回文字").is_visible():
            page.get_by_role("button", name="返回文字").click()
        page.get_by_label("记录内容").wait_for()
        page.get_by_label("添加内容").click()
        page.get_by_role("button", name="文件 / 图片").click()
        inbox_file = f"inbox-correct-{uuid4()}.txt"
        page.get_by_label("选择文件").set_input_files(
            {
                "name": inbox_file,
                "mimeType": "text/plain",
                "buffer": b"# Inbox correction fixture\nimported marker",
            }
        )
        page.get_by_role("button", name="导入文件").click()
        page.get_by_text("文件已进入 Inbox").wait_for()

        _mobile_nav(page).get_by_role("button", name="设置", exact=True).click()
        page.get_by_role("button", name="打开 Inbox").click()
        page.get_by_role("heading", name="所有输入都在这里处理").wait_for()
        inbox_card = page.locator("article").filter(has_text=inbox_file)
        inbox_card.get_by_role("button", name="修正标题 / 类型").click()
        inbox_card.get_by_label("修正标题").fill(f"Corrected {inbox_file}")
        inbox_card.get_by_label("修正内容类型").fill("log")
        inbox_card.get_by_role("button", name="保存修正").click()
        inbox_card.get_by_text("修正已保存到 Entry").wait_for()
        removal = page.evaluate(
            """async (title) => {
                const csrf = decodeURIComponent(document.cookie.split('; ').find((item) => item.startsWith('starmem_csrf=')).split('=')[1]);
                const response = await fetch('/api/v1/entries?limit=100', { credentials: 'include' });
                const data = await response.json();
                const target = (data.items || []).find((item) => item.title === title);
                if (!target) return 'missing';
                await fetch('/api/v1/entries/' + target.id, { method: 'DELETE', credentials: 'include', headers: { 'X-CSRF-Token': csrf } });
                return 'deleted';
            }""",
            f"Corrected {inbox_file}",
        )
        assert removal == "deleted", removal

        _mobile_nav(page).get_by_role("button", name="时间线", exact=True).click()
        marker_card = _entry_cards(page).filter(has_text=marker)
        marker_card.wait_for()
        marker_card.get_by_label("更多操作").click()
        marker_card.get_by_role("button", name="删除", exact=True).click()
        page.get_by_text(marker).wait_for(state="detached")
        assert not console_errors, console_errors
        assert not page_errors, page_errors
        page.screenshot(path="/tmp/starmem-playwright-mobile.png", full_page=True)
        browser.close()
    print("playwright-smoke: passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
