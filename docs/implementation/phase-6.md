# Phase 6 实施记录

## 实际完成

- Web 完成桌面侧栏、移动五项底部导航、Safe Area、触摸目标、focus-visible、reduced-motion、长代码块独立横向滚动和草稿 localStorage 恢复。
- 提供 `manifest.webmanifest`、standalone 元数据、裁剪后的 PNG App Icon（`web/public/starmem-logo.png`）、原图归档（`assets/starmenlogo.png`）、`apple-touch-icon` 链接、Service Worker 注册预留和离线 Shell 回退。
- Settings 页面显示 Provider/模型/限流状态但不回显 Key，支持全局 AI 指令、Prompt Studio、AI Job 重试、Active Memory 和来源范围。
- 结构化 request/job/search 指标接口、备份/恢复脚本、Embedding/Memory 重建命令和操作文档已提供。

## 实际验证

```text
docker compose build web
docker compose exec api pytest -q
scripts/smoke.sh
scripts/backup.sh <temporary-directory>
```

Browser QA 实际检查 375×812、768、1024、1440：页面 `scrollWidth == viewport width`；375px 显示 5 项底部导航，桌面显示侧栏；Capture、Search、Ask、来源跳转、Prompt Studio 页面均可操作，浏览器无 reported errors。备份脚本已实际生成 dump 并用 PostgreSQL 镜像列出 entries/content_units/memory_candidates/prompt_versions 表项。

## 已知限制

真实 iPhone Safari 的 Home Screen 安装、键盘、网络切换和系统 Safe Area 仍需实体设备补验；本地 Chromium 响应式检查不能替代真机结论。恢复脚本为显式确认后的破坏性操作，未在当前数据上执行恢复。
