# native-portability Specification

## Purpose
让用户可以导出并重新导入自己的 StarMem 原生内容，同时保留 Raw-first、Memory 独立性和附件隐私边界。
## Requirements
### Requirement: Native data can be exported in portable formats

系统 MUST 提供 Markdown、JSON、JSONL 和 ZIP 导出；导出 MUST 包含 Raw Entry 及必要来源/派生引用，ZIP MUST 包含原始附件字节。

#### Scenario: Export a portable archive

- **WHEN** 已认证用户请求 ZIP 导出
- **THEN** 系统返回可读数据文件和安全命名的附件，且不包含认证凭据或运行时 Key。

### Requirement: Native export can be imported without destructive overwrite

系统 MUST 接受 StarMem 原生 JSON/JSONL 导入，复用现有 Entry 创建和安全扫描；重复 Raw/title MUST 跳过，不得覆盖、删除或合并既有数据。

#### Scenario: Re-import an export

- **WHEN** 用户再次导入刚导出的 JSON/JSONL
- **THEN** 系统报告 created/skipped 数量，既有 Entry/Memory 保持不变。

### Requirement: Import and export are bounded and secret-safe

系统 MUST 限制导入条数/字节数和导出记录数；接口与文件 MUST 不携带 API Key、Session、密码或完整 Authorization Header。

#### Scenario: Invalid import is rejected

- **WHEN** 导入非 JSON/JSONL 或缺少有效 raw_content
- **THEN** 系统返回可理解错误且不产生半条 Entry。

