## Why

P0 已能可靠保存纯文本，但用户仍需要先手工复制网页、解析 PDF 或整理图片内容，导致重要信息无法低摩擦进入 StarMem。P1 需要把 URL、文件和图片输入纳入同一条 Raw-first、可追溯、可重试的异步处理链路。

## What Changes

- 新增统一输入入口，支持 URL、TXT、Markdown、JSON、YAML、Log、PDF 和图片上传。
- 保存 URL 原地址与网页快照；保存上传文件的原始字节、哈希、媒体类型和处理元数据。
- 为 PDF 提取文本并保留页码；为图片提供本地 OCR Provider，失败时保留原始图片并显示可重试状态。
- 将导入结果映射为 Native Entry/ContentUnit，继续复用现有 Chunk、FTS、Embedding、AI Job 和 Provenance 链路。
- 新增 Inbox，展示 New、Processing、Processed、Failed 状态、错误原因、原始输入和重新处理操作。
- 增加导入任务查询、重试、附件元数据/下载和 URL/文件安全限制；不实现未指定的第三方 Connector。
- 在 Web 中加入 Inbox 入口、导入表单、处理状态和附件/页码来源信息。

## Capabilities

### New Capabilities

- `input-ingestion`: URL、文本类文件、PDF、图片上传及统一导入 API。
- `attachment-ocr`: 原始附件存储、PDF 页级提取、图片本地 OCR 和附件 Provenance。
- `inbox-processing`: 导入任务状态、失败可见性、重试和 Inbox Web 体验。

### Modified Capabilities

- None. P0 的 Source、ContentUnit、Entry、AI Job 和 Search 契约保持兼容；本 change 通过新增字段和能力连接既有链路。

## Impact

- Backend：新增 Attachment/导入字段、Alembic migration、文件存储、URL 抓取、文本/PDF/OCR 解析、导入 API、Worker actor、Inbox API 和 schemas。
- Web：新增 Inbox/导入交互、附件和处理状态展示，并保持现有 Capture/Timeline/Search/Ask 路径不变。
- Runtime：增加本地附件 volume、`python-multipart`、PyMuPDF、Pillow、pytesseract 和 Tesseract OCR runtime；OCR 模型/语言数据只在本地执行。
- Tests/Docs：覆盖原始输入保留、格式解析、页码/来源、OCR 成功/失败、URL 安全、幂等和重试，并更新运行维护文档。
