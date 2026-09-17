# Phase 3 实施记录

## 实际完成

- 内置 `observation_extract`、`classification`、`summary`、`tag`、`entity_extract`、`time_extract`、Project/Topic、Relation、Memory、Salience、Reconcile、Query 和 Answer Prompt，并由 seed 幂等注册。
- Prompt 版本支持 Production/Draft/Archived、User Instructions、Preview、History、Diff、Promote、Restore Default 和 Golden Test；安全契约与 Output Schema 不接受普通模式修改。
- OpenAI-compatible Chat Provider 仅从运行时 Key 读取，默认传递 `chat_template_kwargs.enable_thinking=false`，有 timeout、有限重试和 backoff。
- 解析后的模型输出由严格 Pydantic Schema 校验；不合法输出只将 Job 标记为 `prompt_validation_failed`，不写入派生数据。
- Worker 对每类任务独立记录状态、attempt、Provider、model、latency、token usage 和 error；规则型标识符/时间/标签/实体提取不依赖 Chat。
- User Tag/Entity 覆盖有独立来源优先级，Prompt/Observation/Memory Provenance 保留 Provider、model、Prompt 版本、Schema 和 hash。

## 实际验证

```text
docker compose exec api pytest -q
```

最近一次容器结果为 `20 passed`（含 Mock Provider 的成功/失败 Schema、超时重试、Golden Dataset、用户覆盖、Prompt Draft 隔离和 AI Job 幂等路径）。未注入运行时 Chat Key 时，依赖 Chat 的 Job 会显示 credentials 未配置，不影响 Raw/FTS。

## 已知限制

当前 Prompt Studio 是面向单用户的基础版，未实现 P1 的高级完整 Prompt 克隆和多用户权限；具体模型路由字段已进入 Prompt Version，远程调用仍需用户通过未跟踪 `.env` 或环境变量注入 Key。
