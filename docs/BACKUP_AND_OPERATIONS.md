# 备份与运行维护

## 备份

```bash
scripts/backup.sh
# 或指定目录
scripts/backup.sh backups/manual-20260915
```

备份包含 PostgreSQL 中的 Raw Entry、版本、ContentUnit、Memory、来源和 Prompt Registry，以及 API/Worker 共享 volume 中的原始附件归档。脚本只保存脱敏环境文件，实际 API Key、Session Secret 和密码必须通过独立的运行时密钥管理恢复。Embedding 是可重建派生数据，不应成为恢复原始数据的前置条件。

## 原生数据搬迁

More 页面“数据搬迁”或认证接口可导出当前未删除的 Native Entry：

```text
GET /api/v1/export?format=json|jsonl|markdown|zip&source_scope=all|native|external
```

JSON/JSONL 适合再次导入；Markdown 适合人工阅读；ZIP 另含经 SHA-256 校验的原始附件。导出结果不包含用户、Session、密码、API Key 或运行时配置。导出上限为 10,000 条 Entry。

仅可导入 StarMem 自己生成的 `.json` 或 `.jsonl`：

```text
POST /api/v1/import
Content-Type: multipart/form-data
file: starmem-export.json 或 starmem-export.jsonl
```

单次最多导入 100 条且复用上传字节上限；相同 Raw/title 的未删除 Entry 会报告为 skipped，不覆盖或删除既有数据。新 Entry 复用版本、ContentUnit、AI Job 和本地安全扫描流程。导入接口当前不解包第三方格式或 ZIP 附件；附件字节的完整恢复使用上方数据库/附件备份恢复流程。

## 恢复

恢复会覆盖同名数据库中的对象，必须明确确认目标数据库和备份文件：

```bash
RESTORE_CONFIRM=YES scripts/restore.sh backups/manual-20260915/starmem.dump
docker compose exec api alembic upgrade head
```

恢复脚本会在同目录存在 `attachments.tar` 时一并恢复附件；旧版本仅有数据库 dump 时会明确提示附件字节未恢复。恢复前必须确认目标附件 volume，脚本会清理该 volume 中的现有文件。

恢复后检查 `/health`、登录、Timeline 和全文搜索，再执行 Embedding 重建：

```bash
docker compose exec api python -m app.rebuild_embeddings
```

## 重处理与故障降级

- `POST /api/v1/entries/{id}/reprocess` 创建新的 generation，不修改原始版本。
- `POST /api/v1/ai-jobs/{id}/retry` 只重试对应任务。
- `POST /api/v1/entries/{id}/safety/rescan` 只更新本地安全扫描摘要，不修改 Raw、版本或附件。
- Knowledge Summary 是可重建的 Derived Knowledge；重生成只更新相同范围的 Summary 与来源 metadata。
- Chat 或 Embedding 不可用时，Raw、版本、Timeline 和 FTS 仍可用；UI 会显示失败或降级状态。
- API Key 不进入日志、前端 bundle、备份脱敏配置或仓库文件。
- 附件文件名不会直接作为存储路径，数据库中的 SHA-256 可用于恢复后的完整性检查；定期清理没有数据库记录的孤儿附件。
