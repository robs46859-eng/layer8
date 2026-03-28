import logging

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=logging.INFO if settings.environment != "dev" else logging.DEBUG,
        format="%(message)s",
    )
