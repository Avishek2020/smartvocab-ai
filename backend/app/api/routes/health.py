import redis
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.deps import DB
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: DB) -> JSONResponse:
    checks: dict[str, str] = {}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:  # noqa: BLE001
        checks["database"] = "error"
    try:
        redis.Redis.from_url(get_settings().redis_url, socket_connect_timeout=0.5).ping()
        checks["redis"] = "ok"
    except redis.RedisError:
        checks["redis"] = "unavailable"
    healthy = checks["database"] == "ok"
    return JSONResponse(status_code=200 if healthy else 503,
                        content={"status": "ok" if healthy else "degraded", "checks": checks})
