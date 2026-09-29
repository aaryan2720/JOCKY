from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import api_v1_router, health_router
from app.api.websocket import ws_jobs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown event handling."""
    # Startup: Initialize logging, db pool, etc.
    yield
    # Shutdown: Clean up connections


def create_app() -> FastAPI:
    """Application factory for JOCKY FastAPI Management Server."""
    app = FastAPI(
        title="JOCKY Management Server",
        description="Programmable DFIR Fleet Management, JOCKY DSL Engine & Detection API",
        version=settings.VERSION,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount Route Handlers
    app.include_router(health_router)
    app.include_router(api_v1_router)
    app.include_router(ws_jobs_router)

    return app


app = create_app()
