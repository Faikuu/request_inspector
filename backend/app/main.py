"""Application factory. Run with: uvicorn app.main:app"""

import logging
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import Settings
from app.db import init_db, make_engine, make_session_factory
from app.ratelimit import SlidingWindowLimiter
from app.realtime import StreamHub
from app.routers import hooks, inboxes, stream

logger = logging.getLogger("request_inspector")

SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
    "x-frame-options": "DENY",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
}
DOC_PATHS = ("/docs", "/redoc", "/openapi.json")
HOOK_PATH_PREFIX = "/api/hook/"
HOOK_ALLOWED_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        is_docs = scope["path"].startswith(DOC_PATHS)

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in SECURITY_HEADERS.items():
                    if is_docs and name == "content-security-policy":
                        continue  # the interactive docs load their assets from a CDN
                    if name not in headers:
                        headers[name] = value
            await send(message)

        await self.app(scope, receive, send_with_headers)


class HookCorsMiddleware:
    """Capture URLs are public by design, so browsers may call them from any origin.

    Only preflight requests (OPTIONS with Access-Control-Request-Method) are answered here.
    A plain OPTIONS request is still captured like any other method.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith(HOOK_PATH_PREFIX):
            await self.app(scope, receive, send)
            return

        request_headers = Headers(scope=scope)
        if scope["method"] == "OPTIONS" and "access-control-request-method" in request_headers:
            preflight = Response(
                status_code=204,
                headers={
                    "access-control-allow-origin": "*",
                    "access-control-allow-methods": HOOK_ALLOWED_METHODS,
                    "access-control-allow-headers": request_headers.get("access-control-request-headers", "*"),
                    "access-control-max-age": "600",
                },
            )
            await preflight(scope, receive, send)
            return

        async def send_with_cors(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)["access-control-allow-origin"] = "*"
            await send(message)

        await self.app(scope, receive, send_with_cors)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    if not settings.secret_key:
        settings.secret_key = secrets.token_urlsafe(48)
        logger.warning(
            "RI_SECRET_KEY is not set. Using a random key: viewer sessions end on every restart. "
            "Set RI_SECRET_KEY in backend/.env to keep them."
        )

    engine = make_engine(settings.database_url, echo=settings.sql_echo)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        await init_db(engine)
        try:
            yield
        finally:
            await engine.dispose()

    docs_on = settings.enable_docs
    app = FastAPI(
        title="Request Inspector API",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs" if docs_on else None,
        redoc_url="/redoc" if docs_on else None,
        openapi_url="/openapi.json" if docs_on else None,
    )

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)
    app.state.hub = StreamHub()
    app.state.session_limiter = SlidingWindowLimiter(settings.session_attempts_per_minute, 60)
    app.state.inbox_session_limiter = SlidingWindowLimiter(settings.inbox_session_attempts_per_minute, 60)
    app.state.create_limiter = SlidingWindowLimiter(settings.inbox_creates_per_hour, 3600)
    app.state.hook_limiter = SlidingWindowLimiter(settings.hook_requests_per_minute, 60)

    # Added last = outermost. Hook CORS sits outside the browser CORS policy for the app.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(HookCorsMiddleware)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        detail = "Invalid request"
        errors = exc.errors()
        if errors:
            first = errors[0]
            location = ".".join(str(part) for part in first.get("loc", ()) if part not in ("body", "query", "path"))
            message = str(first.get("msg", "invalid value"))
            detail = f"{location}: {message}" if location else message
        return JSONResponse(status_code=422, content={"detail": detail})

    @app.exception_handler(Exception)
    async def unhandled_error(_request: Request, _exc: Exception) -> JSONResponse:
        # The server still logs the traceback. The client only gets a generic message.
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers=SECURITY_HEADERS,
        )

    @app.get("/api/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(inboxes.router)
    app.include_router(hooks.router)
    app.include_router(stream.router)
    return app


app = create_app()
