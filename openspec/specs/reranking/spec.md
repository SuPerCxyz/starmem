# reranking Specification

## Purpose
TBD - created by archiving change starmem-v2-p1-gap-closure. Update Purpose after archive.
## Requirements
### Requirement: 可配置 Reranker 且失败回退

系统 SHALL 支持可配置 Reranker，默认关闭；启用后对 Hybrid 候选重排，异常时回退既有排序。

#### Scenario: 启用并成功

- **WHEN** Reranker 已配置且返回分数
- **THEN** 结果按重排分数排序并记录指标

#### Scenario: 调用失败

- **WHEN** Reranker 超时或报错
- **THEN** 返回原 Hybrid 排序结果，不返回错误

