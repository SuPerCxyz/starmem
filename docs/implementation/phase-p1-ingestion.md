# P1 输入与导入实施记录

## 实际完成

- Alembic `0007_p1_ingestion` 新增 Attachment、Native 导入关联、幂等键、处理阶段和 ContentUnit 附件来源字段。
- Compose API/Worker 共享 `starmem-storage` volume；附件使用 UUID storage key、SHA-256 和认证下载，原始字节不由 OCR/AI 覆盖。
- 支持 TXT、Markdown、JSON、YAML、Log、PDF、PNG/JPEG/WebP/GIF/BMP/TIFF；文本按 UTF-8、UTF-16、GB18030、Latin-1 安全 fallback 解码。
- PDF 按页生成 ContentUnit 并保留 `page_number`；无文本页使用本地 Tesseract OCR fallback。
- 图片 OCR 使用本地 Tesseract，默认 `eng+chi_sim`；OCR 不可用时附件保留并进入 Failed，可重试。
- URL 仅允许 HTTP/HTTPS，执行 DNS/IP 私网拦截、重定向上限、响应类型/大小/超时限制，并保存 URL HTML 快照。
- 新增 `/api/v1/ingest/url`、`/api/v1/ingest/file`、`/api/v1/inbox`、Inbox retry、附件列表和认证下载接口。
- Web Capture 新增文字/网页 URL/文件图片输入模式；Inbox 显示 New、Processing、Processed、Failed、错误、尝试次数、附件和 Entry 跳转。
- Search/Ask Provenance 现在包含附件 ID、页码、原 URL、最终 URL 和 `file_text`/`pdf_page`/`image_ocr`/`web_page` 类型。
- 备份/恢复脚本已同时处理 PostgreSQL dump 和附件 tar；恢复仍要求显式 `RESTORE_CONFIRM=YES`。

## 实际验证

```text
docker compose exec -T api ruff format --check app tests alembic
docker compose exec -T api ruff check app tests alembic
docker compose exec -T api pytest -q                 # 26 passed, 4 warnings
docker compose build web                             # TypeScript/Vite build passed
scripts/smoke.sh                                     # integration-smoke: passed
python3 tests/playwright_smoke.py                    # playwright-smoke: passed
scripts/backup.sh <temporary-directory>              # backup-attachments: passed
```

额外实跑了 API→Redis→Worker→Inbox→附件下载→Search、实际本地 OCR 图片、实际 PDF 页提取、Ask 来源跳转和页码来源，均通过。测试数据和临时备份已清理。

## 已知限制

- URL 网络抓取的单元测试使用 MockTransport 加安全边界验证；本次未主动抓取真实公网网页。
- 当前 OCR 依赖 Compose 镜像中的 Tesseract 和语言包，不提供云端 OCR；识别质量取决于图片/PDF 清晰度。
- 未实现对象存储、具体第三方 Connector、浏览器插件、原生 iOS、Web Push 和多人权限；这些属于后续独立 change。
- 真机 iPhone Safari、键盘、网络切换和 Home Screen 安装仍需设备验收。
