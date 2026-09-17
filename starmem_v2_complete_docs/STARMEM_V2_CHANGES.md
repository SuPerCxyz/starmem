
# StarMem v2 需求变更摘要

相较上一版，v2 重点新增：

1. **iOS / Mobile P0**
   - iPhone Safari
   - 添加到主屏幕
   - standalone Web App
   - Safe Area
   - Mobile Bottom Navigation
   - 长期登录
   - 草稿保护

2. **External Corpus Architecture**
   - Source
   - External Item
   - ContentUnit
   - Provenance
   - Search Scope
   - 大规模异步 Ingestion 架构
   - P0 只预留，不实现具体 Connector

3. **StarMem Memory Engine**
   - Evidence / Observation / Memory / Knowledge 四层
   - Salience
   - Retrieve-Before-Write
   - Memory Reconcile
   - ADD / SUPPORT / SUPERSEDE / CONFLICT / MERGE / IGNORE
   - Temporal Memory
   - 并发写入保护

4. **Prompt Engine / Prompt Studio**
   - Prompt Registry
   - User Instructions
   - 高级完整 Prompt 编辑
   - Prompt Versioning
   - Diff / Rollback
   - Output Schema Contract
   - Prompt Preview
   - Golden Dataset
   - 用户自定义 Test Case
   - AI 派生结果追踪 model / prompt / schema version
