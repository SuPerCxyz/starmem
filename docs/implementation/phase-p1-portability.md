# P1 Native Portability 实施记录

## 实际完成

- 新增认证 `GET /api/v1/export`，支持 Markdown、JSON、JSONL 和 ZIP；默认过滤软删除 Entry，导出最多 10,000 条。
- JSON/JSONL 保留 Raw、内容/时间/来源字段以及标签、实体、Observation、active/conflicted Memory 引用和附件元数据；Markdown 以稳定 Entry ID 注释保留回溯关系。
- ZIP 包含 `starmem-export.json` 和经数据库 SHA-256 校验的原始附件字节，路径固定为 `attachments/<entry_id>/<attachment_id>-<safe-name>`，下载名按当天日期生成。
- 新增认证 `POST /api/v1/import`，仅接受 StarMem 原生 JSON/JSONL（对象数组、`entries` 包装对象或 JSONL）；单次最多 100 条并复用上传字节限制。
- 导入按未删除 Entry 的 Raw/title 精确去重，重复项只计入 skipped；新项复用 Entry create、EntryVersion、ContentUnit、AI Job 和本地安全扫描，不覆盖或删除已有数据。
- More 页面提供四种下载入口、原生备份文件选择和 created/skipped/error 反馈；导入数据不包含凭据，也不在前端保存密钥。

## 主要接口

```text
GET  /api/v1/export?format=json|jsonl|markdown|zip&source_scope=all|native|external
POST /api/v1/import (multipart file: *.json 或 *.jsonl)
```

`source_scope` 仅影响导出筛选；导入始终进入 `StarMem Native`。第三方 Memos、Obsidian、Notion、Karakeep、ChatGPT、Claude 等格式、CLI/MCP、外部 Connector、多人/RBAC、Graph 和 ZIP 反向解包不在本阶段范围内。

## 安全边界

- 导出序列化白名单字段，不导出 User、UserSetting、Prompt provider credentials、Session、密码、API Key 或 Authorization Header。
- ZIP 附件使用数据库中的存储键读取，并在写入归档前校验 SHA-256；原始文件名只作为安全化后的展示片段。
- 导入拒绝不支持的扩展名、外部 format、非法 JSON、非对象记录和缺少非空 `raw_content` 的记录；单条失败回滚，不产生半条 Entry。
- 新导入仍走原有 Raw-first、Secret Scan、异步派生和远程脱敏链路。

## 实际验证

```text
docker compose exec -T api pytest -q tests/test_p1_portability.py  # 1 passed, 3 warnings
docker compose exec -T api pytest -q                            # 29 passed, 5 warnings
docker compose build web                                          # TypeScript/Vite build passed
python3 tests/playwright_smoke.py                                 # export download + duplicate import + regression passed
```

浏览器测试实际下载 JSON 导出文件，通过文件选择器上传同一条 Raw 的 StarMem JSON，验证 `created=0/skipped=1` 反馈，并继续执行既有 Capture、Search、Ask、Workbench、Inbox 和响应式路径。

## 已知限制

- ZIP 当前用于导出；导入接口只接受 JSON/JSONL，不自动解包 ZIP 或第三方备份。
- 导入最多 100 条，导出最多 10,000 条；导入附件元数据不重新写入附件存储。
- 当前系统仍是单用户边界；外部 Connector、CLI/MCP、多人/RBAC、Graph 等后续跨层能力保持排除。
