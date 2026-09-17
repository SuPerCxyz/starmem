# P1 Mobile Share Target

## Why

StarMem 已有移动端 Capture、文件导入和 Inbox，但从 iOS/Android 分享菜单进入时仍需要手工复制文本或重新选择文件。P1 需要把手机分享动作收敛为可确认的 Capture/Inbox 入口。

## What Changes

- 为 PWA 增加 Web Share Target，接收分享标题、文本、URL 和文件/图片。
- Service Worker 在 `/share` 接收 multipart 分享请求，将短期 payload 安全地交给打开后的 Capture 页面。
- Capture 自动识别分享内容：文本进入文字草稿，URL 进入网页导入，文件/图片进入附件导入；用户可在保存前编辑或取消。
- 分享页面保留原有 CSRF、Session、URL SSRF、上传大小、OCR 和附件完整性边界，不新增外部服务。
- 为 Share Target 增加移动浏览器可验证的 manifest、Service Worker、Capture 和失败/恢复提示。

## Goals / Non-Goals

**Goals:**

- 手机分享文本、网页、图片和文件后，三步内完成确认保存。
- 分享失败或页面刷新时不丢失已接收的短期 payload；读取后删除本地暂存。
- 不绕过现有登录、CSRF、URL 安全和文件限制。

**Non-Goals:**

- 不实现离线 Entry 同步、Web Push、App Badge、相机/语音、Passkey/Face ID。
- 不实现 CLI、MCP、浏览器插件、外部 Connector、多人/RBAC 或 Graph。
- 不把共享内容写入 Service Worker Cache；原始文件只在浏览器短期 IndexedDB 与服务器附件存储中流转。

## Impact

- Web manifest、Service Worker、Share payload 本地存储工具和 Capture UI。
- Browser/Playwright 验证增加 Share Target 元数据、文本/URL 预填和文件分享入口检查。
- Backend API/数据模型不新增公共契约；复用 `/ingest/url`、`/ingest/file` 和现有认证接口。
