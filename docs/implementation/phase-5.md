# Phase 5 实施记录

## 实际完成

- Ask 先用 Regex/Rule 做 intent、关键词、标识符、实体和时间提示理解，再复用统一 Hybrid Search 与 Source Scope。
- 已支持今天、昨天、本周、上周、本月、上个月、最近、前段时间、去年、月份、第一次和最近一次的时间边界/排序提示。
- Context Builder 只使用 bounded Search、ContentUnit 和 Active Memory 来源；Source Citation 返回 Entry、ContentUnit/Chunk、Source、时间、snippet、score 和 jump target。
- Chat 可选：有运行时配置时走 Answer Prompt 和严格 Answer Schema；无 Key、无来源或模型失败时使用可说明的确定性降级/拒答，并明确标识事实与推断。
- Ask Web 页面分离 Answer/Sources，支持来源展开和跳转 Timeline 原文；Search/Ask 均支持 Native/External/All 来源范围。

## 实际验证

已实跑 `POST /api/v1/ask`：有来源时返回 `150W` 和 Entry jump target；无 Chat 时显示确定性来源摘要。后端单测覆盖 Query Understanding、时间预设、来源降级和无来源拒答；全栈 smoke 也覆盖 Ask 来源链路。

## 已知限制

默认未配置独立 Reranker，仅提供可替换 Protocol/Mock；远程 Chat 的最终答案质量取决于用户配置的模型和运行时 Key，真实 Chat 生成未在无 Key 的本地验收中宣称通过。
