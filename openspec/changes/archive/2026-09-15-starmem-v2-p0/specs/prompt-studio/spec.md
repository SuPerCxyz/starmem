## Purpose

让 Prompt 成为可版本化、可测试、可回滚的一等资源，使用户能够调整 AI 指令而不破坏系统安全契约或失去派生结果的可追踪性。

## ADDED Requirements

### Requirement: Prompt registry has layered versioned resources
系统 MUST 注册 Observation、Entity、Temporal、Memory、Salience、Reconcile、Relation、Knowledge、Query Understanding 和 Answer 等 Prompt；最终 Prompt MUST 由 System Safety Contract、Task Prompt、User Instructions 和 Runtime Context 组成。

#### Scenario: Resolve a production prompt
- **WHEN** AI Job 请求 Memory Extract Prompt
- **THEN** 系统解析唯一 Production 版本并组合四层内容，记录版本号、Schema 版本和 Prompt Hash

### Requirement: User instructions are editable without weakening the safety contract
普通模式 MUST 允许编辑全局或单个 Prompt 的 User Instructions，但不得修改系统 Safety Contract；高级完整编辑 MUST 基于 Clone 并显示风险提示。

#### Scenario: Edit user instructions
- **WHEN** 用户修改 Memory Extract 的 User Instructions 并保存
- **THEN** 系统创建新 Draft Prompt Version，旧版本和 Production 版本保持不变

### Requirement: Prompt versions support history and promotion
每次修改 MUST 创建新版本，系统 MUST 支持 History、Diff、Rollback、Promote to Production、Restore Default，并同时保存模型 Provider、模型、temperature、top_p、max_tokens 和 Schema 版本。

#### Scenario: Roll back a prompt
- **WHEN** 用户把 Draft 或 Production Prompt 回滚到历史版本
- **THEN** 系统创建或激活对应版本，不删除历史版本，后续派生结果记录实际使用的版本

### Requirement: Output Schema is validated before persistence
AI 输出 MUST 经过与 Prompt 绑定的 Output Schema 验证；验证失败时禁止写入 Observation、Memory 或其他派生状态，并将错误写入 AI Job。

#### Scenario: Invalid model output
- **WHEN** 模型返回缺少必需字段或包含未允许的 Reconcile Operation
- **THEN** Job 标记 Prompt Validation Failed，数据库不写入该派生结果

### Requirement: Prompt tests do not change production behavior
系统 MUST 提供 Built-in Golden Dataset 和用户自定义 Test Case，支持对 Draft 执行 Test、显示 Passed/Failed、对比 Production 与 Draft；测试或 Draft 不得自动上线。

#### Scenario: Run a draft against golden cases
- **WHEN** 用户对 Draft 执行 Prompt Test
- **THEN** 系统运行固定测试集并展示断言结果，Production 版本保持不变

### Requirement: Derived AI results are traceable to prompt versions
Observation、Memory 和 Knowledge MUST 能按 Prompt 名称、版本、Schema 版本、模型和 Provider 查询或重处理。

#### Scenario: Reprocess after promotion
- **WHEN** 用户 Promote 新 Prompt Version 后重新处理 Entry
- **THEN** 新派生结果记录新版本，历史派生记录仍能显示原来使用的版本
