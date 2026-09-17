# P1 Mobile Share Target 实施记录

## 实际完成

- PWA manifest 新增 `POST /share` Web Share Target，接收 title、text、url 以及 text/image/PDF/JSON/YAML/Markdown 文件。
- Service Worker 只拦截同源 `/share` multipart 请求，将分享内容写入 `starmem-share` IndexedDB 的单个最近 payload，再重定向到 `/?shared=1`；不把原始分享内容写入 Cache Storage。
- 分享 payload 对标题、文本、URL 和文件总字节数设置 20 MiB 上限，最多 4 个文件；超限只返回可理解的错误状态，不创建半条 Entry。
- Capture 启动时读取并删除 payload：文本预填文字模式，URL 预填网页模式，文本同时带 URL 时提供“改为网页 URL”，文件/图片恢复为内存 File 并进入文件模式。
- 分享后的保存继续复用 `/entries`、`/ingest/url`、`/ingest/file`，因此沿用 Session/CSRF、URL SSRF、上传大小、OCR、附件哈希和 Inbox 状态边界。
- 页面刷新后的文字仍由既有 Capture localStorage 草稿保护；IndexedDB 或 File 构造不可用时显示提示，普通输入入口继续可用。

## 验证

```text
docker compose build web                             # TypeScript/Vite build passed
python3 tests/playwright_smoke.py                    # Share Target + text/URL/file + PWA + responsive passed
```

浏览器测试通过 Service Worker 实际发送同源 multipart `/share`，验证最终重定向、文本/URL 预填、文件名恢复、既有 Capture→Search→Ask→Workbench→Inbox 链路和 375/768/1024/1440 无横向溢出。

## 已知限制

- Share Target 依赖浏览器已安装/启用 PWA 和 Service Worker；首次安装后的真实 iOS/Android 系统分享菜单仍需真机验收。
- 多文件分享当前保留上限并恢复第一个文件到 Capture；单文件图片/PDF/文本文档流程完整复用现有 Inbox。
- 本阶段不提供离线 Entry 同步、Push、相机/语音、Passkey、CLI/MCP、浏览器插件、外部 Connector 或多人权限。
