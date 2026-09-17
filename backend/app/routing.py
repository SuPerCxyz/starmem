"""Task-level model routing with Prompt and user-setting precedence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UserSetting

TASK_ALIASES = {
    "classification": "classification",
    "classify": "classification",
    "summary": "summary",
    "memory_extract": "memory",
    "memory": "memory",
    "answer": "chat",
    "chat": "chat",
    "embedding": "embedding",
    "reranker": "reranker",
}


def task_route(db: Session, task: str, prompt) -> tuple[str | None, str | None]:
    """Return provider/model; custom Prompt wins, then user route, then builtin defaults."""
    if prompt.created_by != "system" and (prompt.provider or prompt.model):
        return prompt.provider, prompt.model
    settings = db.scalar(select(UserSetting).order_by(UserSetting.updated_at.desc()))
    routes = settings.model_routing if settings else {}
    route = routes.get(TASK_ALIASES.get(task, task)) if isinstance(routes, dict) else None
    if isinstance(route, dict):
        return str(route.get("provider") or prompt.provider or "openai-compatible"), str(
            route.get("model") or prompt.model or ""
        ) or None
    return prompt.provider, prompt.model
