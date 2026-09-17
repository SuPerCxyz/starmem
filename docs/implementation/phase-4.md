# Phase 4 实施记录

## 实际完成

- Observation、Memory Candidate、Canonical Memory、MemorySource 和 Knowledge Hook 分层持久化。
- Salience 对稳定事实、临时测试和 ignore 分类；Candidate 先按 normalized subject/predicate/value Retrieve，再进行确定性 Reconcile。
- Apply 只允许 ADD、SUPPORT、SUPERSEDE、CONFLICT、MERGE、IGNORE；Active Scope 唯一索引、PostgreSQL advisory transaction lock 和来源唯一检查共同保护并发写入。
- Superseded、Conflicted、Expired、Deleted 查询和手工 Confirm/Delete API 已提供，历史 Memory 不被静默删除。

## 实际验证

测试覆盖 `150W` durable、`175W` episodic、相同值 SUPPORT 去重、`180W → 150W` SUPERSEDE、`8080/8081` CONFLICT、两 Worker 同 scope 并发以及 Knowledge 不替代 Atomic Memory。最近一次容器测试结果包含在 `20 passed` 中。

## 已知限制

Knowledge 当前提供安全的来源校验/创建 Hook，尚未启用自动长文知识整合；Relation 仍由独立 AI Job/Relation 表承载，不把 Graph UI 纳入 P0。
