# mobile-share Specification

## Purpose
让移动端用户可以通过系统分享菜单把文本、URL、图片或文件快速送入 StarMem Capture/Inbox。
## Requirements
### Requirement: Share Target receives supported mobile content

系统 MUST 在 PWA manifest 中声明 Share Target，并接收标题、文本、URL 以及图片/文件；接收请求 MUST 只由同源 Service Worker 处理。

#### Scenario: Share text or URL

- **WHEN** 用户从手机分享一段文本或网页
- **THEN** StarMem 打开 Capture，预填文字或 URL，用户确认后复用现有 Entry/URL ingestion 流程。

#### Scenario: Share an image or file

- **WHEN** 用户从手机分享图片或支持的文件
- **THEN** StarMem 打开 Capture 的文件入口，保留文件名/MIME 并允许用户确认上传到 Inbox。

### Requirement: Shared payload stays bounded and recoverable

系统 MUST 对 Share payload 的数量和字节数设置本地上限；读取后 MUST 删除短期 payload，不得将原始分享内容写入 Service Worker Cache。

#### Scenario: Share payload exceeds the local bound

- **WHEN** 分享内容超过本地上限或 IndexedDB 不可用
- **THEN** 页面显示可理解的失败提示，普通 Capture/Import 入口仍可用且无半条 Entry。

### Requirement: Share flow preserves existing safety boundaries

系统 MUST 继续使用现有认证、CSRF、URL SSRF 防护、上传大小、OCR、附件哈希和 Inbox 状态流；分享入口不得绕过这些边界。

#### Scenario: Shared URL or file is saved

- **WHEN** 用户确认保存分享内容
- **THEN** URL 仍经过后端安全抓取，文件仍经过现有上传/解析/OCR/附件流程，并能从 Inbox/Entry 查看状态。

