# 本地/兼容 Chat 配置

StarMem 的 Chat 调用使用 OpenAI-compatible `/v1` 接口；API Key 只从运行时环境读取，不能写入仓库、镜像或日志。

当前验证过的配置为：

- Base URL：`https://llm.soocoo.xyz/v1`
- Chat model：`qwen35-4b`
- 默认关闭思考：`chat_template_kwargs.enable_thinking=false`

## 配置

复制 `.env.example` 为未跟踪的 `.env`，只在 `.env` 中填写实际 Key：

```bash
cp .env.example .env
STARMEM_CHAT_API_KEY='<runtime-secret>' docker compose up -d --build
```

或者通过 shell 环境注入，不落盘：

```bash
export STARMEM_CHAT_API_KEY='<runtime-secret>'
docker compose up -d --build
```

不要把 Key 放到 `docker-compose.yml`、前端变量、提交记录、截图或调试日志中。生产环境还应设置随机的 `STARMEM_SESSION_SECRET`、开启 `STARMEM_COOKIE_SECURE=true`，并将 CORS 限制为实际 Web 来源。

## Embedding 分工

该 Chat 服务只承担文本生成；它的 Embedding 路径不可用时，StarMem 使用独立的本地 FastEmbed 模型 `BAAI/bge-small-zh-v1.5`（512 维）完成语义索引。Embedding 模型按首次使用懒加载，模型不可用不会阻断 Raw 写入和 PostgreSQL 全文检索。

## 最小连通性检查

使用临时环境变量执行，不要把真实 Key 写进命令历史：

```bash
curl -sS "$STARMEM_CHAT_BASE_URL/models" \
  -H "Authorization: Bearer $STARMEM_CHAT_API_KEY"
```

StarMem API 的状态接口会报告 `chat_configured`，但不会回显 Key 或请求内容：

```bash
curl -sS http://localhost:18000/api/v1/status
```

不同任务可以在登录后的 `PATCH /api/v1/settings` 中单独指定 provider/model。设置响应只包含路由名称和模型，不包含 Key：

```json
{
  "model_routing": {
    "summary": {"provider": "openai-compatible", "model": "qwen35-4b"},
    "memory": {"provider": "openai-compatible", "model": "qwen35-4b"}
  }
}
```
