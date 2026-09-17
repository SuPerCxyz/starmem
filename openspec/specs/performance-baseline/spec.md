# performance-baseline Specification

## Purpose
TBD - created by archiving change starmem-v2-p1-gap-closure. Update Purpose after archive.
## Requirements
### Requirement: 可复现性能基线

系统 SHALL 提供基准脚本，测量 Raw 保存、全文、Hybrid 与 Ask 本地检索延迟，并输出可记录的结果。

#### Scenario: 运行基准

- **WHEN** 用户按指定规模运行脚本
- **THEN** 脚本输出各操作的 P50/P95 与实际数据规模

#### Scenario: 资源不足

- **WHEN** 无法达到 100k Entry / 500k Chunk 目标规模
- **THEN** 文档记录实际规模、降级原因与剩余风险，不宣称达标

