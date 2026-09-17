# Design

## Export contract

```text
GET /api/v1/export?format=markdown|json|jsonl|zip&source_scope=all
```

每个原生记录序列化为 `entry` 对象：

- Raw fields：id、title、raw_content、content_format、content_type、source_uri、event_time、created_at、updated_at。
- Derived context：tags、entities、observations、active/conflicted Memory references。
- Attachment metadata：id、original_filename、media_type、size_bytes、content_hash、metadata_json。

Export 读取软删除过滤后的 Entry，最多 10,000 条，结果是当时的数据快照；JSON/JSONL 使用 ISO 8601，Markdown 以稳定 ID 注释保留回溯关系。ZIP 文件名使用 `starmem-export-YYYYMMDD.zip`，附件写入 `attachments/<entry_id>/<attachment_id>-<safe-name>`。

## Import contract

```text
POST /api/v1/import
Content-Type: multipart/form-data
file: StarMem JSON or JSONL
```

- 最多 100 条记录，单次请求复用现有 upload 限制。
- 只接受对象数组、`{"entries": [...]}` 或每行一个 JSON 对象；不接受任意字段作为 SQL/路径。
- 必须有非空 `raw_content`，字段长度复用 `EntryCreate` 约束；`event_time_*` 仅接受合法 ISO 时间。
- 用 Raw/title 精确匹配跳过当前未删除记录，避免重复；新记录经 `create_entry_service` 生成版本、ContentUnit、AIJob 和 EntrySafetyScan。
- 附件字节不在 JSON/JSONL Import 中导入；ZIP 附件恢复仍由备份/恢复脚本负责，避免在本阶段引入临时文件解包路径风险。

## Privacy and safety

Export 响应不包含 User、UserSetting、Prompt provider credentials 或任何运行时 secret。导入内容仍保留 Raw-first 语义和本地 Secret Scan，远程发送仍走现有 `redact_secrets`。
