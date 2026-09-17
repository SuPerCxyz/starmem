import logging
import time
from collections import defaultdict, deque
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from sqlalchemy import text
from starlette.responses import JSONResponse

from app.api import router
from app.config import get_settings
from app.db import SessionLocal
from app.logging import configure_logging
from app.metrics import observe, snapshot

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title="StarMem API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Request-ID"],
)
app.include_router(router)

# ponytail: the single-process API is intentionally protected with a small in-memory limiter.
_rate_limit_buckets: defaultdict[str, deque[float]] = defaultdict(deque)
_rate_limit_lock = Lock()
_rate_limit_window = 60.0


def _rate_limit_exempt(request: Request) -> bool:
    return request.method == "OPTIONS" or request.url.path in {"/health", "/api/v1/status"}


def _allow_request(request: Request) -> bool:
    limit = settings.rate_limit_per_minute
    if limit <= 0 or _rate_limit_exempt(request):
        return True
    client_host = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _rate_limit_lock:
        bucket = _rate_limit_buckets[client_host]
        while bucket and now - bucket[0] >= _rate_limit_window:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if not _allow_request(request):
        return JSONResponse(
            {"detail": "Rate limit exceeded"},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": str(int(_rate_limit_window))},
        )
    return await call_next(request)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    observe("request", latency_ms=latency_ms)
    logger.info(
        "%s %s %s",
        request.method,
        request.url.path,
        response.status_code,
        extra={"request_id": request_id, "latency_ms": latency_ms},
    )
    return response


def _database_healthy() -> bool:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception:  # Health response intentionally avoids connection details.
        return False


def _redis_healthy() -> bool:
    try:
        Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1).ping()
        return True
    except Exception:
        return False


@app.get("/health")
def health(response: Response) -> dict[str, object]:
    dependencies = {"database": _database_healthy(), "redis": _redis_healthy()}
    healthy = all(dependencies.values())
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if healthy else "degraded", "dependencies": dependencies}


@app.get("/api/v1/status")
def api_status() -> dict[str, object]:
    return {
        "name": "StarMem",
        "version": app.version,
        "chat_configured": bool(
            settings.chat_base_url and settings.chat_model and settings.chat_api_key
        ),
        "chat_model": settings.chat_model or None,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.embedding_model,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
    }


@app.get("/api/v1/metrics")
def metrics() -> dict[str, dict[str, float | int]]:
    return snapshot()
