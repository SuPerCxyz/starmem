# P1 Native Import / Export

## Why

StarMem 已能保存 Raw、版本、派生数据和附件，但用户还不能从应用内导出可迁移文件，也不能把自己的 StarMem JSON/JSONL 备份重新导入。P1 需要提供不依赖第三方服务的可搬迁闭环。

## What Changes

- 新增认证 Export 接口，提供 Markdown、JSON、JSONL 和 ZIP 四种格式。
- JSON/JSONL 保留 Raw Entry、时间、内容类型、来源 URI 以及可解释的标签、实体、Observation、Memory 和附件元数据。
- ZIP 在可读导出文件之外包含原始附件字节，并用安全的 Entry/Attachment ID 命名。
- 新增仅面向 StarMem 原生 JSON/JSONL 的批量 Import；导入复用现有 Entry create、Secret Scan、AI Job 和 Native Source 流程，并跳过已存在的相同 Raw/title。
- Web More 页面提供导出下载和原生 JSON/JSONL 导入反馈。

## Non-Goals

- 不实现 Memos、Obsidian、Trilium、Notion、Karakeep、ChatGPT、Claude 等第三方格式适配。
- 不导出或导入 API Key、Session、密码、Cookie 或运行时环境。
- 不覆盖、删除或修改既有 Entry/Memory；导入只新增或跳过。
