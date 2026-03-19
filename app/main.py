"""FastAPI application entry-point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import create_app_context
from app.api.routes import init_routes, router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    ctx = create_app_context(settings)
    init_routes(ctx)
    app.state.ctx = ctx

    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Casino Property Concierge",
        description=(
            "AI-powered conversational agent that answers guest questions "
            "about a specific casino property."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api/v1")

    return app


app = create_app()
