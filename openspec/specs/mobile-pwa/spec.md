# mobile-pwa Specification

## Purpose
让 StarMem 在桌面、iPhone Safari 和 iOS 主屏幕 Web App 中都能完成记录、Timeline、搜索和问记忆，并保证触摸、长内容和草稿输入可用。
## Requirements
### Requirement: Mobile is a first-class responsive experience
Web UI MUST 在 375px、768px、1024px 和 1440px 等宽度下可用；移动端 MUST 采用单列内容布局、触摸目标至少 44px、无横向页面溢出，辅助 Metadata 使用 Drawer、Sheet 或折叠区域。

#### Scenario: Use core flows on a phone viewport
- **WHEN** 用户在窄屏 Safari 视口打开 StarMem
- **THEN** Capture、Timeline、Search 和 Ask 均可操作，页面主体不横向溢出，固定导航不遮挡内容

### Requirement: PWA metadata and standalone shell are present
系统 MUST 提供 `manifest.webmanifest`、App Icon/`apple-touch-icon`、`display: standalone` 和 Service Worker 预留；启动页应能以独立 Web App 形态加载。

#### Scenario: Inspect home-screen metadata
- **WHEN** 浏览器读取 PWA manifest 并以 standalone 模式启动
- **THEN** StarMem 名称、图标、主题色和 standalone 配置有效，应用不依赖桌面导航才能进入核心页面

### Requirement: Safe areas and mobile navigation are respected
系统 MUST 使用 iOS Safe Area Insets，提供不超过五项的移动底部导航（记录、时间线、搜索、问记忆、更多），并让来源引用、按钮、标签和输入控件适合触摸。

#### Scenario: Device with a bottom home indicator
- **WHEN** 用户在存在底部 Home Indicator 的 iPhone 上查看页面
- **THEN** Bottom Navigation 和编辑器不会被安全区遮挡，正文可以滚动到完整可见

### Requirement: Capture drafts survive common interruptions
系统 MUST 自动保存 Capture 草稿；刷新、切后台或短暂断网后应尽可能恢复未提交文本，并且核心登录状态不得只依赖 localStorage 中的 Token。

#### Scenario: Recover an interrupted draft
- **WHEN** 用户输入长文本后刷新页面或暂时失去网络
- **THEN** 草稿仍可恢复，已提交 Entry 与未提交草稿不会互相覆盖

