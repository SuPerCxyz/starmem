# Phase 2 实施记录

## 实际完成

- `chunk_text` 按 Markdown heading、段落、围栏代码、日志、列表、表格、JSON/YAML 识别；超长普通文本在空白/标点/行边界切分，代码和 Traceback 优先保持完整。
- `EntryChunk` 保存类型、token 估算、原文 offset、ContentUnit 归属和 512 维向量；PostgreSQL 已建立 ivfflat cosine indexes。
- FastEmbed 懒加载 `BAAI/bge-small-zh-v1.5`；Chat `/embeddings` 不承担向量任务，Chat 与本地 Embedding Provider 分离。
- `fulltext`、`semantic`、`hybrid` 三种 API 模式可用。Hybrid 对关键词/向量分数归一化并使用环境权重，完整标识符命中有额外优先级；无模型时返回 `semantic_available=false` 并降级 FTS。
- API 结果返回 Entry、ContentUnit、Chunk、Source、snippet、score、match reason 和外部来源字段。

## 实际验证

```text
docker compose exec api pytest -q
docker compose exec api python -m app.rebuild_embeddings
```

固定 Fixture 覆盖中文改写检索、因果 Hybrid 排序、精确标识符优先、分块边界和无 Embedding 降级。最终容器测试结果为 `20 passed`。首次本地模型加载实际完成，并生成 512 维 Chunk 向量；一次中文改写查询返回目标 Entry，观测相似度约 `0.6652`。

## 已知限制

首次模型加载会产生下载延迟；模型缓存通过 Compose volume 共享。中文 PostgreSQL FTS 仍辅以 ILIKE/trigram。默认未启用独立 Reranker，Provider Contract 和 Mock 已提供。
