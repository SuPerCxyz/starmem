# attachment-ocr Specification

## Purpose
保留附件作为不可变原始证据，并将 PDF 页和图片 OCR 结果转换为可检索、可引用、可重处理的 ContentUnit，而不让派生文本取代原始文件。
## Requirements
### Requirement: Attachments preserve original evidence

系统 MUST 以不可变文件对象保存上传附件的字节、媒体类型、原始文件名、大小、SHA-256 内容哈希和所属 Entry；附件下载 MUST 经过认证，且原始文件不得由 OCR、摘要或用户编辑覆盖。

#### Scenario: Preserve an uploaded image

- **WHEN** 用户上传一张图片并等待处理完成或失败
- **THEN** 系统仍可下载与最初上传字节一致的图片，并可通过 Entry 查看其附件元数据和处理状态

#### Scenario: Deduplicate identical attachment bytes

- **WHEN** 同一 Entry 重试处理同一附件
- **THEN** 系统复用内容哈希对应的附件对象，不创建重复文件，并保留新的处理尝试记录

### Requirement: PDF extraction preserves page provenance

系统 MUST 从可解析 PDF 提取文本并按页生成有序 ContentUnit；每个页级单元 MUST 保留页码、附件标识和文本偏移或证据片段，使 Search/Ask 能够引用具体页码。解析失败 MUST 保留原始 PDF。

#### Scenario: Search a PDF page

- **WHEN** 用户上传包含多个页面的 PDF，且关键词只出现在第 3 页
- **THEN** 搜索结果命中第 3 页 ContentUnit，并返回附件来源和页码 3 的跳转/引用信息

#### Scenario: Reject a malformed PDF without data loss

- **WHEN** 上传的 PDF 无法解析
- **THEN** 原始 PDF 附件和 Entry 仍然存在，导入任务标记 Failed，并展示可重试的解析错误

### Requirement: Image OCR runs locally and is optional to persistence

系统 MUST 通过可替换的本地 OCR Provider 处理图片文字，记录 OCR Provider、语言、耗时和结果状态；OCR 失败、模型缺失或语言不可用不得删除原始图片或阻断其他 Raw/FTS 能力，且图片内容不得未经用户配置发送远程 LLM。

#### Scenario: Extract text from an image locally

- **WHEN** 用户上传包含清晰文字的图片且本地 OCR Provider 可用
- **THEN** 系统生成 OCR 文本 ContentUnit，标记其来源为该图片附件，并使文本进入全文检索/后续 Embedding 队列

#### Scenario: OCR provider is unavailable

- **WHEN** 本地 OCR Provider 不可用或处理超时
- **THEN** 系统保留图片附件，任务进入 Failed 或 retryable 状态，Entry 仍可打开并显示 OCR 未完成

### Requirement: Derived attachment text remains distinguishable

系统 MUST 区分原始附件、PDF 提取文本和 OCR 文本的 `unit_type`/元数据；Ask 来源 MUST 能标明证据来自原始文件、PDF 页或图片 OCR，不得把派生文本标记为用户原始输入。

#### Scenario: Cite OCR evidence

- **WHEN** Ask 使用图片 OCR 文本回答问题
- **THEN** 来源中明确显示图片附件、OCR 标记和命中的文本片段，并可跳转到对应 Entry/附件

