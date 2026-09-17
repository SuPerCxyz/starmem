# Design

## Share flow

```text
手机分享菜单
      ↓ POST /share (multipart/form-data)
Service Worker 读取 title/text/url/files
      ↓ IndexedDB 短期 payload
302 /?shared=1
      ↓
Capture 读取并删除 payload
      ↓ 用户确认
文字 → POST /entries
URL  → POST /ingest/url
文件 → POST /ingest/file
```

## Storage boundary

- IndexedDB 数据库名为 `starmem-share`，对象仓库只保存一个最近 payload 和各文件的 `ArrayBuffer`、文件名、MIME、大小。
- 读取成功或用户取消后删除 payload；Service Worker 不把 payload 放进 Cache Storage。
- 每个 payload 限制 20 MiB 总字节数、最多 4 个文件、单文件大小仍由后端上传限制最终校验；超限时重定向并显示可恢复错误。
- 未登录时仍由现有 LoginScreen 接管；payload 暂存不会成为认证 token。

## Manifest and Service Worker

- 使用一个 `POST` Share Target，以 `multipart/form-data` 同时覆盖 text/url/file。
- `share_target.action` 为 `/share`；Service Worker 只拦截同源 POST `/share`，其他请求保留当前网络优先、Shell fallback 行为。
- 文件转为可结构化存储的元数据和 ArrayBuffer，Capture 使用 `new File()` 重新生成浏览器上传对象。

## Capture integration

- App 启动时只在 URL 含 `shared=1` 时读取 payload，避免每次加载访问 IndexedDB。
- 文本优先级为 `text`，空文本时使用 `url`；同时存在 URL 和文本时优先显示文本，并提供“改为网页 URL”操作。
- 文件分享自动切换到文件模式并展示文件名；不能通过安全限制写入 file input 时，使用内存 `File` 状态提交。
- 用户仍可编辑文字、修改 URL、替换文件或取消，不修改现有 Capture 草稿自动保存策略。

## Failure and recovery

- IndexedDB 不可用、payload 过大或解析失败：Capture 显示明确提示，普通文字/URL/文件入口仍可用。
- 分享文件上传失败：保留 Capture 中的内存 File，用户可重试；不重复创建 Entry，后端现有 Idempotency-Key 机制仍可继续扩展。
- 页面刷新后共享 payload 已读取并删除时，已进入 Capture 的文字依靠现有 localStorage 草稿保护；文件需要用户重新分享或重新选择。
