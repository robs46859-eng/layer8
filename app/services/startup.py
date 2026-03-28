import logging

from app.core.config import Settings
from app.services.readiness import ReadinessService

logger = logging.getLogger(__name__)


def run_startup_checks(settings: Settings, readiness_service: ReadinessService) -> dict:
    result = readiness_service.check()
    logger.info(
        {
            "event": "startup_checks_completed",
            "app_name": settings.app_name,
            "environment": settings.environment,
            "backend_mode": settings.backend_mode,
            "status": result["status"],
            "checks": result["checks"],
        }
    )
    if result["status"] != "ok" and settings.startup_checks_strict:
        raise RuntimeError("startup dependency checks failed")
    return result
