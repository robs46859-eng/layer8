import logging

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        force=True,
    )
    for logger_name in [
        "boto3",
        "botocore",
        "urllib3",
        "s3transfer",
        "sqlalchemy.engine",
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
