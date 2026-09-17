## Context

当前项目已有 Project、Topic、Entity、Observation、Memory、Knowledge 和 AI Derivation Meta 表，但 Project/Topic 主要由 Worker 写入，缺少面向用户的聚合查询；搜索条件也只存在于请求中。Secret Scanner 当前只负责远程 Prompt 前的脱敏，尚未保存安全扫描结果。

## Goals / Non-Goals

**Goals:**

- 使用既有 Evidence/Observation/Memory 关系计算 Project、Topic、Entity 的可解释统计，不引入第二套事实数据。
- Saved Search 保存查询表达式和过滤器；Smart View 只是一组服务端定义的动态查询，不复制 Entry。
- Secret Scan 只保存类型、位置和是否检测到等摘要，不保存检测出的凭据文本；原文、版本和附件不变。
- 相似检测提供建议而非自动合并；Knowledge Summary 记录来源 Entry/Memory 并保持可重建。
- 模型路由设置可被 Worker 读取，Provider Key 仍只来自运行时环境。

**Non-Goals:**

- 不实现 Graph UI、Topic/Project Evolution、高级 Memory Consolidation、主动提醒、多人/RBAC 或具体第三方同步。
- 不自动修改/删除 Raw Entry，不把相似 Entry 静默合并，不把 Knowledge Summary 当作 Atomic Memory。

## Decisions

### 1. 聚合优先，保持数据单一事实源

Project/Topic 详情从 Observation 的 `project`/`topic` 记录、Entry 和 Active Memory 即时聚合；Entity 详情从 EntryEntity、Relation 和 Entry 聚合。Project/Topic 表继续作为名称和状态目录，不新增重复的 Entry 外键。

备选方案是新增多张显式映射表；这会与现有 AI generation 和人工覆盖状态产生双写不一致，本阶段不采用。

### 2. Saved Search 与 Smart View 分离

Saved Search 新增轻量表保存名称、query、scope 和 JSON filters；Smart View 使用代码定义的稳定 ID 与查询参数，结果实时计算。用户可以保存/删除 Saved Search，但不能修改内置 Smart View 的语义。

### 3. Secret Scan 只存摘要

新增 EntrySafetyScan 一对一记录 `detected`、finding types、line/column 摘要、scanner version 和时间。扫描器继续支持 password/token/API key/private key/cookie/authorization 等模式；任何发送给 Chat 的内容仍走现有 `redact_secrets`，安全扫描结果不替代 Raw。

### 4. 相似检测使用可解释候选

对已保存 Entry 使用 PostgreSQL trigram/ILIKE 候选，必要时再复用 Chunk 向量分数；API 返回相似度、匹配片段和 Entry ID。保存动作永远先完成，检测失败只返回空建议，不影响 Capture。

### 5. 路由设置与 Prompt 版本共同决定模型

UserSetting 增加 task→model/provider JSON；Worker 在解析 Prompt 时优先使用 Prompt Version 明确路由，其次使用用户任务路由，再回退到全局 Chat 配置。任何未配置的 Provider 仍显示失败/降级，不把 Key 写入设置或响应。

### 6. Knowledge Summary 可重建且带来源

Summary 从指定 Project/Topic/时间范围的 Entry、Observation 和 Active Memory 生成确定性 Markdown 草稿，保存为 Knowledge 并在 metadata 中记录 `entry_ids`、`memory_ids`、生成时间和摘要范围。暂不让小模型自由生成无来源长文。

## Risks / Trade-offs

- [历史 Entry 缺少 Project/Topic Observation] → 页面显示空统计，不伪造分类；重新处理可补齐。
- [Secret 正则存在误报/漏报] → 只作本地提示，显示类型和位置，允许用户继续保存；远程发送仍采用独立脱敏防线。
- [Trigram 对中文和短文本不稳定] → 与完整标识符/ILIKE/向量候选组合，返回解释性分数，不把阈值当事实。
- [路由设置与 Prompt 版本冲突] → 明确优先级并在 AI Job provenance 记录最终 provider/model。
- [Knowledge Summary 可能过时] → 标记 derived、保留来源 ID，并提供重新生成；不修改 Atomic Memory。

## Migration Plan

1. 运行 `0008_p1_workbench`，新增 EntrySafetyScan、SavedSearch 和 UserSetting 路由字段。
2. 旧 Entry 可按需/批量补扫 Secret，缺失扫描记录不影响现有数据。
3. 部署 API/Worker 后验证 Project/Topic/Entity、Saved Search、Smart View、相似检测和回顾接口。
4. 新增 Knowledge Summary 只写 Derived Knowledge；回滚时删除新增表/字段即可，Raw/EntryVersion/Memory 不变。

## Open Questions

无。Graph、多人权限和第三方 Connector 仍由后续独立 change 处理。
