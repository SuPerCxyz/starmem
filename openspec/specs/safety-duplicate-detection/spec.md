# safety-duplicate-detection Specification

## Purpose
在保留原始输入的前提下，帮助用户识别可能的敏感信息和高度相似记录，并提供可解释、可跳转、可忽略的安全提示。
## Requirements
### Requirement: Secret detection runs locally and preserves Raw

系统 MUST 在本地扫描 Password、Token、API Key、AK/SK、Private Key、Cookie、Authorization Header 和数据库凭据等模式，保存检测类型/位置/扫描版本摘要；扫描不得修改 Raw Entry、附件或历史版本。

#### Scenario: Detect a token in a captured log

- **WHEN** Entry 原文包含疑似 Authorization Header 或 API Token
- **THEN** Entry 显示敏感信息提示和类型/位置摘要，但原文仍可查看，且发送远程 Chat 前使用脱敏文本

#### Scenario: Scan content without secrets

- **WHEN** Entry 不包含已知敏感模式
- **THEN** 安全扫描状态为 clean，不阻断保存或检索

### Requirement: Similar entries are advisory only

系统 MUST 在 Entry 保存后提供相似 Entry 候选、相似度和匹配原因；用户仍可保留当前 Entry、查看候选或稍后处理。系统 MUST 不自动删除、覆盖或合并 Raw Entry。

#### Scenario: Save a repeated configuration

- **WHEN** 用户保存与历史配置高度相似的新 Entry
- **THEN** 系统仍保存新 Entry，并展示相似候选及其时间/跳转入口

#### Scenario: Similarity service is unavailable

- **WHEN** trigram 或 Embedding 检索不可用
- **THEN** Entry 保存成功，重复建议为空或标记不可用，不影响 Timeline/FTS

