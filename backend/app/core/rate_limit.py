"""Fixed-window rate limiter backed by Redis, with an in-memory fallback when Redis is unreachable
(development and tests). Production should always run with Redis."""
import logging
import threading
import time
from collections import defaultdict

import redis
from fastapi import Request

from app.core.config import get_settings
from app.core.errors import AppError

log = logging.getLogger("smartvocab")
_mem: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))
_lock = threading.Lock()
_client: redis.Redis | None = None


def _redis() -> redis.Redis | None:
    global _client
    if _client is None:
        try:
            c = redis.Redis.from_url(get_settings().redis_url, socket_connect_timeout=0.3, socket_timeout=0.3)
            c.ping()
            _client = c
        except redis.RedisError:
            return None
    return _client


def reset_memory_limits() -> None:
    """Clear all rate-limit counters (used by tests)."""
    with _lock:
        _mem.clear()
    r = _redis()
    if r is not None:
        for key in r.scan_iter("rl:*"):
            r.delete(key)


def rate_limit(scope: str, limit: int | None = None):
    def dependency(request: Request) -> None:
        max_req = limit or get_settings().auth_rate_limit_per_minute
        ip = request.client.host if request.client else "unknown"
        window = int(time.time() // 60)
        key = f"rl:{scope}:{ip}:{window}"
        count: int
        r = _redis()
        if r is not None:
            try:
                count = int(r.incr(key))
                if count == 1:
                    r.expire(key, 65)
            except redis.RedisError:
                r = None
        if r is None:
            with _lock:
                w, c = _mem[key]
                count = c + 1
                _mem[key] = (window, count)
        if count > max_req:
            raise AppError(429, "rate_limited", "Too many requests, please wait a minute.")

    return dependency
