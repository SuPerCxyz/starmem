# P1 Knowledge Workbench 实施记录

## 实际完成

- Alembic `0008_p1_workbench` 新增 `EntrySafetyScan`、`SavedSearch` 和 `UserSetting.model_routing`；Raw、EntryVersion、Attachment 和 Atomic Memory 的生命周期保持不变。
- Project、Topic、Entity 列表和详情从既有 Observation、EntryEntity、Relation 及 Memory 来源即时聚合，返回首次/最近出现、Entry/Memory 数量、来源 ID 和相关对象；未分类目录只显示零统计，不创建假关系。
- 本地 Secret Scanner 扫描 credential、Authorization、Private Key、Cookie、云凭据和数据库 URI，只保存类型、行列位置、哈希、扫描版本和时间；远程 Chat 仍使用独立脱敏防线。
- 相似 Entry 使用 PostgreSQL `pg_trgm`，数据库函数不可用时降级为本地有界序列相似度；结果仅为建议，不自动覆盖、合并或删除 Raw。
- Saved Search 保存查询、来源范围和过滤器定义，结果每次从当前数据重新执行；Smart View 使用稳定 ID，覆盖问题、解决方案、TODO、决策、测试/性能、最近修改、未解决问题、新/冲突 Memory 和失败 AI Job。
- Review 支持今天、最近七天、最近三十天和自定义范围，返回有界统计与可跳转来源；Knowledge Summary 使用确定性 Markdown，metadata 记录 `scope_type`、范围、`entry_ids`、`memory_ids` 和生成时间，可按同一范围重生成。
- Web 新增 Knowledge Workbench、Saved Search、Smart View、回顾、Summary 来源跳转，并在 Timeline 展开 Entry 时显示安全摘要和相似记录建议；移动端保持单列和五项底部导航。

## 主要接口

```text
GET  /api/v1/projects                GET  /api/v1/projects/{id}
GET  /api/v1/topics                  GET  /api/v1/topics/{id}
GET  /api/v1/entities                GET  /api/v1/entities/{id}
GET  /api/v1/reviews?period=week
GET  /api/v1/smart-views             GET  /api/v1/smart-views/{view_id}
GET  /api/v1/saved-searches          POST/PATCH/DELETE /api/v1/saved-searches
GET  /api/v1/saved-searches/{id}/results
GET  /api/v1/entries/{id}/safety     POST /api/v1/entries/{id}/safety/rescan
GET  /api/v1/entries/{id}/similar
GET  /api/v1/knowledge               POST /api/v1/knowledge/summaries
```

### 任务模型路由

设置只接受任务到 `provider`/`model` 的映射，不接受 API Key、Authorization Header 或连接凭据：

```json
{
  "model_routing": {
    "summary": {"provider": "openai-compatible", "model": "qwen35-4b"},
    "memory": {"provider": "openai-compatible", "model": "qwen35-4b"}
  }
}
```

优先级为：自定义 Prompt Version 明确路由 → 用户任务路由 → 全局运行时 Chat 配置。最终 provider/model 写入 AI Job 和 `AiDerivationMeta`；Key 仍只来自容器运行时环境。

## 隐私与维护

- 安全扫描不会阻断保存，也不把疑似值写入 `entry_safety_scans`；原文、版本、附件和搜索内容保持可访问。
- 旧 Entry 可通过 `POST /api/v1/entries/{id}/safety/rescan` 按需补扫。删除 Entry 仍是软删除，Smart View、Workbench 和搜索默认排除。
- Summary 是 `derived` Knowledge，重生成只更新 Summary 内容和来源 metadata，不改变 Raw 或 Memory 状态；没有来源时仍生成可解释的空统计草稿。
- `pg_trgm`/Embedding/Chat 不可用时，保存、Timeline 和 FTS 不被阻断；相似建议为空或使用有界本地 fallback，AI Job 失败可在 AI Processing Failed View 中重试。

## 实际验证

```text
docker compose exec -T api pytest -q                 # 28 passed, 4 warnings
docker compose build web                             # TypeScript/Vite build passed
python3 tests/playwright_smoke.py                    # passed: Workbench/Saved Search/Safety/Responsive
```

## 已知限制

- 当前 Workbench 是单用户边界，不提供多人/RBAC、Graph UI、Topic/Project Evolution 或高级 Memory Consolidation。
- Smart View 使用确定性规则和当前派生字段，不把小模型输出当作新的事实。
- 相似度是解释性提示，不提供自动去重决策；中文短文本仍可能出现误报或漏报。
