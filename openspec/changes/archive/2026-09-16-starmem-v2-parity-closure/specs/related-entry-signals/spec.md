## Purpose

让 Related Entry 的建议来源可解释：除语义/相似度外，显式使用共享实体、标签、Project、Topic、同 Error 与同 Host 等确定性信号。

## ADDED Requirements

### Requirement: 确定性关联信号

系统 SHALL 基于共享实体、共享标签、同 Project、同 Topic、同 Error、同 Host 与语义相似度计算相关记录，并返回命中理由。

#### Scenario: 共享实体
- **WHEN** 两条 Entry 共享同一实体
- **THEN** 相关记录结果包含该候选并说明命中原因

#### Scenario: 多信号排序
- **WHEN** 同一候选命中多个信号
- **THEN** 排序体现信号强度，理由包含全部命中项

#### Scenario: 无关联
- **WHEN** 没有任何信号命中
- **THEN** 返回空列表而不是低质量候选
