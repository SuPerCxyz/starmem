## Purpose

为 StarMem 提供可重复的 Tabler Typography 验收能力，证明字体样式、实际渲染字体、文字几何尺寸和截图结果在固定环境下与官方 Reference 一致。

## ADDED Requirements

### Requirement: 确定性 Typography Fixture

系统 MUST 提供不出现在正常导航中的 `/__ui/tabler-typography-fixture` 测试页面，并使用 Tabler 官方 class 展示标题、导航、正文、CJK/Latin 混排、数字、Code、Button、Input、Select、Badge、Status、Card、Table、Small text 和 Link。

#### Scenario: Fixture 可直接访问
- **WHEN** 校验工具访问 `/__ui/tabler-typography-fixture`
- **THEN** 页面无需业务数据即可渲染固定文本、固定顺序和固定 DOM 标识，且不会出现在正常 Sidebar 导航中

#### Scenario: Fixture 文本固定
- **WHEN** Fixture 被重复采集
- **THEN** 关键文字、UUID、时间样本和代码样本不依赖随机值、当前时间或 API 数据

### Requirement: 官方字体栈与 CJK fallback

StarMem MUST 继承 pinned Tabler 的默认 Latin、字号、字重、行高、字距和 OpenType 设置；由于官方 Latin stack 不覆盖完整中文 glyph，系统 MAY 仅在其后追加明确的 CJK fallback，并 MUST 在全站保持顺序一致。

#### Scenario: Latin 与数字字体
- **WHEN** 浏览器渲染 Fixture 的 Latin 和数字样本
- **THEN** StarMem 使用与 Tabler Reference 相同的首选 Latin 字体栈、字号、字重、行高、字距和 feature settings

#### Scenario: CJK fallback
- **WHEN** 浏览器渲染中文或中英文混排样本
- **THEN** StarMem 使用记录过的 CJK fallback，且不同页面/组件不会随机选择未记录的中文字体

#### Scenario: Code monospace
- **WHEN** 浏览器渲染 `service: starmem` 或命令样本
- **THEN** StarMem 使用与 Tabler Reference 相同的官方 monospace stack

### Requirement: 自动 Typography Fidelity 校验

系统 MUST 提供自动化校验，分别比较 Tabler Reference Fixture 与 StarMem Fixture 的 computed typography、Chromium 实际 rendered fonts、关键文本 bounding boxes 和同尺寸截图；Computed Style 与 Rendered Font 的强约束失败时命令 MUST 以非零退出。

#### Scenario: Computed Style Diff
- **WHEN** 工具在 light/dark 和四个固定 viewport 采集同一 Fixture
- **THEN** 对 `font-family`、`font-size`、`font-weight`、`font-style`、`line-height`、`letter-spacing`、`font-feature-settings`、`text-transform`、`text-rendering` 输出差异，除记录过的 CJK fallback 外不得存在差异

#### Scenario: Rendered Font Diff
- **WHEN** 工具通过 Chromium CDP 获取关键文本节点的 platform fonts
- **THEN** Latin、数字和 monospace 与 Reference 首选字体一致，CJK 只允许记录中的 fallback，并输出实际字体证据

#### Scenario: Bounding Box Diff
- **WHEN** 工具比较标题、导航、按钮、输入、Badge、正文和 Code 的 `x/y/width/height`
- **THEN** 结果在浏览器像素舍入容差内一致，明显高度或宽度漂移使校验失败

#### Scenario: Screenshot Diff
- **WHEN** 工具完成字体加载并在相同 viewport、DPR、locale、theme 下截图
- **THEN** 输出 Reference、StarMem 和 diff PNG，像素差异按固定且记录的严格规则判定，不得通过 mask、隐藏或放宽阈值掩盖差异

### Requirement: 服务、网络与页面错误审计

校验工具 MUST 从 `TABLER_REFERENCE_URL` 与 `STARMEM_URL` 读取目标地址，检查服务可用性，并在目标不可用时按记录的本地命令启动服务；字体请求失败、字体解码错误、CORS 错误、`console.error` 或 `pageerror` MUST 使校验失败。

#### Scenario: 双服务可用
- **WHEN** Reference 或 StarMem 地址不可访问
- **THEN** 工具尝试启动对应本地服务并等待 URL 可访问，仍不可用则以非零退出

#### Scenario: 字体网络健康
- **WHEN** 页面请求字体资源
- **THEN** 每个字体响应为 HTTP 200 且没有 request failure；如果使用系统字体没有字体网络请求，输出零请求的明确证据

#### Scenario: 浏览器错误
- **WHEN** 校验期间出现 `console.error`、`pageerror`、OTS parsing、decode 或 CORS font error
- **THEN** 工具记录错误并以非零退出

### Requirement: 真实页面 Typography Audit

Fixture 通过后，工具 MUST 打开真实的 `/capture`、`/timeline`、`/search`、`/ask` 和 `/settings` 页面，审计 body、page title、nav、form-control、button、badge 和可见 code 的 typography，覆盖 light/dark 及四个固定 viewport。

#### Scenario: 页面无 Typography override
- **WHEN** 真实页面审计完成
- **THEN** 任何页面均不得出现未记录的 font-family、font-size、font-weight、line-height、letter-spacing 或 font-feature-settings 覆盖

#### Scenario: 全部 viewport 与主题
- **WHEN** 页面审计运行于 `1440x1000`、`1920x1080`、`390x844`、`430x932` 的 light/dark 环境
- **THEN** 所有页面和主题均生成可审计结果并通过 console、font network 与 overflow 检查

### Requirement: 审计产物与退出码

校验 MUST 生成 `artifacts/ui/reference/`、`artifacts/ui/starmem/`、`artifacts/ui/diff/`、`tabler-typography-style-diff.json`、`tabler-rendered-fonts.json` 和 `page-typography-audit.json`；全部条件通过返回 0，任一强约束失败返回非零。

#### Scenario: 成功产物
- **WHEN** 所有 Typography 检查通过
- **THEN** 产物包含每个 viewport/theme 的截图、style diff、rendered font、bounding box、network/console 摘要，并返回 0

#### Scenario: 失败产物
- **WHEN** 任一强约束失败
- **THEN** 工具保留失败上下文和 diff 产物，并返回非零，不得只输出“known issue”后返回成功
