import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.router_ai import router_ai
from app.router_auth import router_auth
from app.router_category import router_category
from app.router_client import router_client
from app.router_orders import router_order
from app.router_payment import router_payment
from app.router_products import router_product
from app.router_review import router_review
from app.router_transaction import router_transaction
from app.router_websocket import router_websocket
from core.config import settings
from core.redis import redis_client
from database.database import async_session_maker
from services.ai.gemini import close_http


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await close_http()


app = FastAPI(title="Online Shop", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "https://bohdan-shop.duckdns.org",
    settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

logger = logging.getLogger(__name__)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health", tags=["System"])
async def health() -> JSONResponse:
    """Liveness and dependency check used by Docker and the load balancer."""
    checks: dict[str, str] = {}

    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    healthy = all(value == "ok" for value in checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ok" if healthy else "degraded", **checks},
    )


app.include_router(router_payment)
app.include_router(router_websocket)
app.include_router(router_product)
app.include_router(router_client)
app.include_router(router_order)
app.include_router(router_transaction)
app.include_router(router_auth)
app.include_router(router_category)
app.include_router(router_ai)
app.include_router(router_review)