# inbox-processing Specification

## Purpose
让用户能够观察所有 URL/文件导入的处理生命周期，区分已处理、进行中和失败状态，并安全地重试失败任务而不产生重复 Entry 或附件。
## Requirements
### Requirement: Inbox exposes import lifecycle states

系统 MUST 提供 Inbox 列表和详情，至少支持 New、Processing、Processed、Failed 四种状态，并返回输入名称/URL、Entry、附件、创建时间、最近尝试、错误原因和下一步操作。

#### Scenario: Review recent imports

- **WHEN** 用户打开 Inbox
- **THEN** 系统按最近导入时间展示 URL/文件项目、当前状态和对应 Entry，不要求用户在保存前选择项目或分类

#### Scenario: Inspect a failed import

- **WHEN** 某项 URL、PDF 或 OCR 处理失败
- **THEN** Inbox 显示稳定的错误摘要、失败阶段、尝试次数和重试操作，原始输入仍可访问

### Requirement: Import processing is asynchronous and observable

系统 MUST 在保存原始输入后异步执行抓取、解析、OCR、ContentUnit、Chunk 和 Embedding 等步骤；每次尝试 MUST 记录状态、开始/结束时间、阶段和错误，且 API 在排队时不得等待 AI 或 OCR 完成。

#### Scenario: Capture returns before processing finishes

- **WHEN** 用户提交 URL、PDF 或图片
- **THEN** API 在原始输入和导入任务落库后返回，Inbox 先显示 New/Processing，后台完成后更新为 Processed 或 Failed

### Requirement: Retry is safe and idempotent

系统 MUST 支持对 Failed 或 retryable 导入执行重试；重试 MUST 复用原始附件/URL 和 Entry，增加尝试次数，重新生成缺失的派生 ContentUnit/Job，不得复制原始证据。

#### Scenario: Retry a failed OCR job

- **WHEN** 用户修复本地 OCR 配置后点击失败图片的重试
- **THEN** 系统保留同一 Entry 和附件，创建新的处理尝试，成功后状态变为 Processed 并更新 OCR ContentUnit

#### Scenario: Concurrent retry requests

- **WHEN** 用户或两个客户端同时请求同一个导入项目重试
- **THEN** 系统至多启动一个同一阶段的有效处理尝试，最终状态和派生数据保持一致

### Requirement: Inbox actions preserve source boundaries

Inbox 可以打开 Entry 原文、附件和 URL 来源，但 MUST 不允许通过导入处理修改外部网站或上传附件原始字节；用户编辑只创建 EntryVersion，并保留导入证据。

#### Scenario: Edit an imported entry

- **WHEN** 用户编辑已导入 Entry 的展示文本
- **THEN** 系统创建新的 EntryVersion，原始附件/URL 快照和导入元数据仍保持不变

