## ADDED Requirements

### Requirement: Prompt 草案克隆与 Layer 2 编辑

Prompt Studio SHALL 支持克隆内置 Prompt 为可编辑草案，并允许编辑 Layer 2 Task Prompt；系统安全契约与 Output Schema 保持只读。

#### Scenario: 克隆内置 Prompt
- **WHEN** 用户克隆内置 Prompt
- **THEN** 生成含 Task Prompt 的 Draft 版本，Production 版本不受影响

#### Scenario: 编辑 Task Prompt
- **WHEN** 用户修改 Draft 的 Task Prompt 并保存
- **THEN** 新版本记录新的 prompt_hash，旧版本仍可查看

### Requirement: 模型参数版本化编辑

Prompt Studio SHALL 允许在界面编辑 Draft 的 provider、model、temperature、top_p 与 max_tokens，并随版本一起保存。

#### Scenario: 保存模型参数
- **WHEN** 用户修改模型参数并保存 Draft
- **THEN** 该版本保存参数值且不影响 Production 版本

### Requirement: 用户自定义 Test Case

Prompt Studio SHALL 支持用户创建、查看、修改与删除自定义 Test Case，内置 Test Case 不允许删除。

#### Scenario: 新增自定义 Test Case
- **WHEN** 用户为某 Prompt 新增 Test Case
- **THEN** 该用例出现在列表并可参与 Draft 测试

#### Scenario: 删除内置用例
- **WHEN** 用户尝试删除内置 Test Case
- **THEN** 系统拒绝并说明原因
