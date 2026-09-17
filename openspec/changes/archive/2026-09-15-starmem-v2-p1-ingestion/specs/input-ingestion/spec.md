## Purpose

让用户可以把网页、文本文件、PDF 和图片以低摩擦方式保存到 StarMem，并让每种输入都进入统一的 Raw-first Entry、检索和来源追踪流程。

## ADDED Requirements

### Requirement: Unified import accepts supported input types

系统 MUST 提供统一的导入能力，接受 HTTP/HTTPS URL 以及 TXT、Markdown、JSON、YAML、Log、PDF 和常见图片文件。导入请求 MUST 可携带可选标题和客户端幂等键；不支持的媒体类型、扩展名或超过大小限制的输入 MUST 被拒绝并返回可理解的错误。

#### Scenario: Import a text file

- **WHEN** 用户上传 UTF-8 Markdown、JSON、YAML 或 Log 文件
- **THEN** 系统创建一个 Native Entry，保留解码后的原文、格式类型、原始文件附件和可追溯的导入任务

#### Scenario: Reject an unsupported upload

- **WHEN** 用户上传不在允许列表中的文件类型或超过配置大小限制的文件
- **THEN** 系统不创建可见 Entry，返回明确的校验错误，且不执行 AI 或外部网络处理

#### Scenario: Repeat an import with an idempotency key

- **WHEN** 客户端用相同幂等键重复提交同一导入请求
- **THEN** 系统返回原导入任务和 Entry 标识，不创建重复附件、Entry 或处理任务

### Requirement: URL import creates a durable snapshot

系统 MUST 保存用户提交的原始 URL，并在允许的 HTTP/HTTPS 范围内抓取网页快照。快照 MUST 记录标题（若可提取）、正文、抓取时间、最终 URL 和原始响应类型；网页后续失效不得影响已保存快照。

#### Scenario: Save a reachable web page

- **WHEN** 用户提交一个可访问的 HTTP/HTTPS URL
- **THEN** 系统创建 Native Entry，保存原 URL、正文快照和附件/来源元数据，并异步进入后续解析、Chunk、Embedding 和 AI 处理

#### Scenario: Handle an unavailable web page

- **WHEN** URL 请求超时、返回不可接受状态码或正文超过限制
- **THEN** 系统保留导入请求和可用的 URL 元数据，任务进入 Failed，用户可以看到原因并重试，不伪造网页正文

#### Scenario: Block unsafe URL targets

- **WHEN** URL 指向本机回环、链路本地、私有、保留地址或非 HTTP/HTTPS 协议
- **THEN** 系统拒绝抓取，不向该目标发起请求，并返回安全校验错误

### Requirement: Imported entries reuse the native processing contract

成功导入的 URL 或文件 MUST 使用 Native Source 创建或关联 Entry 和至少一个 ContentUnit；其原文 MUST 可通过 Timeline、Full Text Search 和 Ask 检索，且导入不得覆盖用户原有 Entry。

#### Scenario: Search an imported document

- **WHEN** PDF、文本文件或网页快照导入完成并处理成功
- **THEN** 用户可以按全文或语义搜索命中其 Entry，并获得对应文件/网页来源、时间和证据片段

#### Scenario: AI is unavailable during import

- **WHEN** Chat、Embedding 或 Worker 暂时不可用
- **THEN** 原始附件、URL 元数据和已提取原文仍被保存，导入任务和后续 AI Job 分别显示可重试状态

### Requirement: Import metadata is visible and bounded

系统 MUST 保存原始文件名、媒体类型、大小、内容哈希、导入时间和处理状态等元数据；用户界面和 API MUST 不回显运行时凭据，并 MUST 对正文、文件名和 URL 展示设置明确的长度边界。

#### Scenario: Inspect an imported item

- **WHEN** 用户打开导入 Entry 或 Inbox 项目
- **THEN** 系统显示输入类型、处理状态、文件/URL 元数据和可用的原文入口，但不显示任何 Provider Key 或内部认证凭据
