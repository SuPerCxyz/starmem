## Context

P0 已有 Native Source、Entry/EntryVersion、ContentUnit、EntryChunk、AIJob、Dramatiq Worker 和 Search/Ask Provenance。当前入口只接受已经由用户粘贴到 JSON 请求中的文本，`IngestionJob` 只覆盖外部快照的基础契约，尚无附件字节、导入生命周期或解析器。

## Goals / Non-Goals

**Goals:**

- 在不改变 P0 文本 Capture 契约的前提下，增加 URL 和文件导入。
- 保留不可变原始附件/URL 证据，并把可提取文本映射到 Native Entry 和 ContentUnit。
- 使用异步 Worker 执行 URL 抓取、PDF 解析、OCR、Chunk 和 Embedding；API 只负责校验、原始输入落库和排队。
- 让 PDF 页面、图片 OCR 和 URL 快照在 Search/Ask 中可区分并可引用。
- 提供可观察、可重试、幂等的 Inbox 生命周期。

**Non-Goals:**

- 不接入特定第三方知识库、邮件、IM、GitHub 或 Calendar Connector；本阶段仅实现 URL 和本地上传入口。
- 不实现对象存储/S3、多租户权限、浏览器插件、原生 iOS App 或 Web Push。
- 不让 OCR、摘要或 AI 修改原始附件；不对外部网站执行写操作。

## Decisions

### 1. Native Entry + Attachment 双层保存

用户主动导入的 URL/文件统一创建 Native Entry，Entry 保存可检索文本和 `source_uri`，Attachment 保存原始字节。这样沿用 P0 的 Timeline/Search/Ask 入口，同时避免把二进制或 OCR 文本误当成用户手写原文。外部系统未来仍使用 P0 的 ExternalItem/ContentUnit，不在本阶段混入 Entry。

备选方案是只保存 ExternalItem 或只保存提取文本；前者无法满足用户导入体验和 Timeline，后者会丢失原始证据，因此不采用。

### 2. 本地受控文件存储

新增 `STARMEM_STORAGE_PATH`，默认位于 API/Worker 共享的 `/var/lib/starmem/attachments` volume。文件名使用随机 UUID，数据库只保存相对 storage key、SHA-256、媒体类型、大小和原始名称；下载经过 API 认证，不通过 Nginx 静态暴露。备份同时保存 PostgreSQL dump 和附件 tar，Embedding/Chunk 等派生数据仍可重建。

备选方案是直接把二进制放进 PostgreSQL；这会放大 dump、连接和查询成本，不适合后续大文件，因此不采用。

### 3. 解析器和 Provider 分离

文本类文件使用确定性的 UTF-8/安全 fallback 解码；PDF 使用本地 PDF 文本提取并按页生成 ContentUnit；图片和无文本 PDF 页面通过可替换的 `OCRProvider` 调用本地 Tesseract。OCR 语言、超时和启用状态由配置控制，远程 Chat Provider 不参与 OCR。

备选方案是让 Chat 视觉模型承担 OCR；这会增加外部依赖、泄露风险和失败面，与 Raw-first/本地处理约束冲突。

### 4. 导入生命周期和幂等

扩展 `IngestionJob` 以关联 Entry/Attachment、输入类型、阶段、幂等键、attempt、错误和时间戳。API 先保存 Attachment/URL 元数据和空或已知的 Entry，再发送 `process_ingestion`；Worker 使用数据库行锁/状态检查确保同一任务只有一个活动尝试。重试只重用原始输入和 Entry，派生 ContentUnit/AIJob 以 generation/upsert 重建。

状态采用 `new → processing → processed | failed`；排队后可直接显示 Processing，失败保留输入和错误，不把失败伪装为成功。

### 5. URL 安全和内容边界

只允许 `http`/`https`，限制响应字节、重定向次数和抓取超时；每次重定向的目标都重新校验 DNS 解析出的 IP，拒绝 loopback、private、link-local、reserved、multicast 和 unspecified 地址。HTML 使用轻量正文提取器去除脚本/样式，保存最终 URL、标题和抓取时间；不执行脚本、不上传表单、不向目标写入。

备选方案是直接把 URL 交给通用爬虫；其 SSRF、资源上限和脚本执行面更大，不适合自托管个人数据服务。

### 6. API 及 Web 兼容

保留 `/api/v1/entries` 纯文本 Capture；新增 `/api/v1/ingest/url`、`/api/v1/ingest/file`、`/api/v1/inbox` 和认证附件下载接口。Web 在 Capture 中增加输入类型选择，并在现有 More 区域提供 Inbox 入口，避免破坏已验收的五项主导航。

## Risks / Trade-offs

- [OCR 语言包和 Tesseract 在轻量镜像中增加体积] → 仅安装配置的基础语言包，OCR 懒执行；缺少语言时明确 Failed，原图仍可用。
- [URL 抓取仍可能遇到 DNS 重绑定或恶意超大响应] → 限制每次解析/连接/响应大小，关闭脚本和写操作，并在每次 redirect 重新执行地址校验；后续可加入独立沙箱。
- [导入文本更新 Entry 会新增 ingestion version] → 保留初始版本和附件证据，UI 标明版本来源，不覆盖用户后续手工版本。
- [本地 volume 与 PostgreSQL dump 可能恢复不一致] → 备份脚本在同一时间窗口生成 dump 与附件归档，恢复文档要求同时恢复并检查哈希；附件缺失时 Entry 仍可查询但显示证据不可用。
- [不同 PDF/图片格式解析质量差异] → 以输入状态和错误为真实结果，保留原始文件；测试覆盖可解析文本 PDF、OCR 成功和 Provider 不可用。

## Migration Plan

1. 构建包含 `python-multipart`、PyMuPDF、Pillow、pytesseract 和 Tesseract 语言包的 API/Worker 镜像，创建附件 volume。
2. 执行 Alembic migration，新增 Attachment 表以及 IngestionJob 的导入关联/幂等字段；旧 P0 数据不迁移内容，默认状态保持不变。
3. 部署 API/Worker 后验证文本文件、URL、PDF 和图片导入，检查 Inbox、Search/Ask Provenance 和附件下载。
4. 备份恢复必须同时处理数据库 dump 与附件 tar；若需要回滚，先停止 Worker，恢复旧数据库，旧版本可忽略新表但不能保留无法解释的 API 配置。

## Open Questions

无。第三方 Connector、对象存储和多人权限已明确留给后续独立 change，不影响本阶段实现。
