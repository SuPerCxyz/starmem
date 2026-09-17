# Built-in Prompt resources

运行时内置 Prompt 资源位于 `backend/app/prompts/builtin.json`，通过 `python -m app.seed` 同步到 PostgreSQL Prompt Registry。根目录保留此入口，便于后续按任务拆分资源文件；用户自定义版本只写入数据库，不覆盖内置安全契约。
