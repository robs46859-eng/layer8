import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import admin_router
from app.api.billing import (
    billing_router,
    customer_billing_router,
    stripe_webhook_router,
)
from app.api.pilot import admin_pilot_router, pilot_router
from app.api.routes import router
from app.api.spatial import spatial_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.readiness import ReadinessService
from app.services.startup import run_startup_checks

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    readiness_service = ReadinessService(settings)
    logger.info(
        {
            "event": "app_starting",
            "app_name": settings.app_name,
            "environment": settings.environment,
            "backend_mode": settings.backend_mode,
            "startup_checks_enabled": settings.startup_checks_enabled,
            "startup_checks_strict": settings.startup_checks_strict,
        }
    )
    if settings.startup_checks_enabled:
        startup_result = run_startup_checks(settings, readiness_service)
        app.state.startup_readiness = startup_result
    else:
        app.state.startup_readiness = {
            "status": "skipped",
            "backend_mode": settings.backend_mode,
            "checks": {},
        }
    yield
    logger.info({"event": "app_stopping", "app_name": settings.app_name})


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Idempotency-Key",
        ],
    )
    app.include_router(router)
    app.include_router(admin_router)
    app.include_router(billing_router)
    app.include_router(customer_billing_router)
    app.include_router(stripe_webhook_router)
    app.include_router(spatial_router)
    app.include_router(pilot_router)
    app.include_router(admin_pilot_router)
    return app


app = create_app()
