import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analytics, auth, health, users, vocabulary
from app.core.config import get_settings
from app.core.errors import register_error_handlers

log = logging.getLogger("smartvocab")


def create_app() -> FastAPI:
    s = get_settings()
    logging.basicConfig(level=s.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = FastAPI(
        title=s.app_name, version="0.1.0",
        description="AI-powered multimodal vocabulary learning platform. Phase 1: auth, vocabulary, dashboard.",
        docs_url="/docs", redoc_url="/redoc", openapi_url=f"{s.api_prefix}/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware, allow_origins=s.cors_origin_list, allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Content-Type", "Authorization"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        log.info("%s %s %s %.1fms rid=%s", request.method, request.url.path, response.status_code,
                 (time.perf_counter() - start) * 1000, rid)
        return response

    register_error_handlers(app)
    for r in (health.router, auth.router, users.router, vocabulary.router, analytics.router):
        app.include_router(r, prefix=s.api_prefix)
    return app


app = create_app()
