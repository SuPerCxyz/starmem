# ai-enrichment-memory Specification

## Purpose
把原始证据安全地转化为可追踪 Observation、可演化 Memory 和带来源的自然语言答案，同时保证模型不能直接改写或覆盖事实数据。
## Requirements
### Requirement: AI enrichment is asynchronous and observable
系统 MUST 在 Raw Entry 保存成功后异步执行分类、摘要、标签、实体、时间、项目/主题、Embedding、Memory 和关联任务；每个任务 MUST 有状态、尝试次数、Provider、模型、耗时、错误和重试入口。

#### Scenario: Enrichment starts after capture
- **WHEN** 用户保存 Entry
- **THEN** API 先返回 Entry，Timeline 显示 Processing，后台任务随后更新各项状态

#### Scenario: Retry a failed job
- **WHEN** Provider 暂时失败且用户点击重新处理
- **THEN** 新尝试被记录并在成功后更新派生数据，失败原因可见且不会重复生成相同 Tag、Entity、Relation 或 Memory

### Requirement: AI metadata respects user overrides
系统 MUST 区分 AI Generated、User Confirmed AI 和 User Created，并遵循 User Created > User Confirmed AI > AI Generated；用户手工修改或确认的字段在重新处理时不得被 AI 覆盖。

#### Scenario: Reprocess after manual tag edit
- **WHEN** 用户把 AI 标签改为自定义标签后重新处理 Entry
- **THEN** 自定义标签保留，AI 只能补充未被人工锁定的派生数据

### Requirement: Derived data records generation provenance
每个 Observation、Memory 和 Knowledge 派生结果 MUST 记录 Provider、模型、Prompt 名称/版本、Schema 版本、Prompt Hash 和生成时间；Raw Entry 永远保持独立。

#### Scenario: Inspect derived result provenance
- **WHEN** 用户查看某条 Memory 的生成详情
- **THEN** 系统显示其来源 Entry 以及生成该结果的模型、Prompt 版本和 Schema 版本

### Requirement: Memory uses explicit layers and lifecycle
系统 MUST 区分 Evidence、Observation、Memory Candidate、Canonical Memory 和 Knowledge。Memory MUST 支持 Active、Superseded、Conflicted、Expired、Deleted 状态及 recorded_at、observed_at、valid_from、valid_to、superseded_at 等时间信息，并保留所有历史证据。

#### Scenario: Durable memory from a final configuration
- **WHEN** 用户记录“V100 最终固定限制到 150W”
- **THEN** 系统生成 subject=V100、predicate=power_limit、value=150W 的 Active durable Memory，并关联原始 Entry

#### Scenario: Temporary observation does not replace durable memory
- **WHEN** Active Memory 为 V100 power_limit=150W，用户记录“刚才临时测试 175W”
- **THEN** 175W 被标记为 episodic 或不进入 durable Memory，150W 不被 Supersede

### Requirement: Memory reconciliation is finite and deterministic at apply time
模型只能提出 ADD、SUPPORT、SUPERSEDE、CONFLICT、MERGE 或 IGNORE；系统 MUST 在写库前验证 Schema、目标存在性、权限/状态、唯一性和证据来源，并由事务完成最终 Apply。

#### Scenario: Same memory value adds support
- **WHEN** 新 Candidate 与现有 Memory 的 subject、predicate 和 value 相同
- **THEN** 系统保留一个 Canonical Memory 并追加 supporting source，不创建重复 Active Memory

#### Scenario: Explicit update supersedes history
- **WHEN** 新内容明确表示 V100 从 180W“后来最终改成 150W”
- **THEN** 180W 标记 Superseded，150W 为 Active，180W 记录保留且可追溯

#### Scenario: Ambiguous different values become conflict
- **WHEN** 两条记录分别声明 Lumen 默认端口为 8080 和 8081，且没有明确更新关系
- **THEN** 系统不得静默覆盖，相关 Memory 标记 Conflicted，并提供人工确认入口

### Requirement: Memory reconciliation is protected against concurrent writes
系统 MUST 对相同 Memory Scope 使用事务、唯一约束和乐观版本或等效串行化，确保并发 Worker 不产生重复 Active Memory 或丢失证据。

#### Scenario: Two workers reconcile one scope
- **WHEN** 两个 Worker 同时处理 V100:power_limit 的相同 Candidate
- **THEN** 最终只有一个有效 Active Memory，所有支持来源均保留，冲突可重试而不破坏历史

### Requirement: Ask answers are source-grounded
`POST /api/v1/ask` MUST 进行查询理解、关键词/实体/时间检索、Hybrid Retrieval、可选 Rerank 和 Context Build，返回答案、置信度、事实/推断标识和可点击来源；没有可靠来源时不得伪造确定事实。

#### Scenario: Ask returns current memory with citation
- **WHEN** 用户询问“我的 V100 最后设置多少瓦”且历史有 180W Superseded 和 150W Active
- **THEN** 答案为 150W，引用包含 150W 的 Raw Entry，不把 180W 当作当前结论

#### Scenario: Ask distinguishes inference
- **WHEN** 检索结果只支持部分结论，模型需要做合理推断
- **THEN** 推断被明确标记，Sources 与 AI Answer 分开显示

