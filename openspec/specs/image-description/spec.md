# image-description Specification

## Purpose
TBD - created by archiving change starmem-v2-p1-gap-closure. Update Purpose after archive.
## Requirements
### Requirement: 图片描述为可选派生且失败不阻断

系统 SHALL 通过可插拔 ImageDescriptionProvider 为图片 Entry 生成描述；未启用或不可用时 SHALL 保留 OCR 文本并标注降级原因。

#### Scenario: Provider 可用

- **WHEN** 图片描述已启用且模型返回合法结果
- **THEN** 生成 `image_description` 观测并记录派生 meta

#### Scenario: Provider 不可用

- **WHEN** 图片描述未配置或调用失败
- **THEN** 图片与 OCR 原文仍保存，Entry 显示降级原因，AI Job 记录失败状态

