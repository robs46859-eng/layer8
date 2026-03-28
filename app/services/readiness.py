from collections.abc import Callable

import boto3
import redis
from sqlalchemy import text

from app.core.config import Settings
from app.db.session import get_engine


class ReadinessService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def check(self) -> dict:
        if self.settings.backend_mode != "self_hosted":
            return {
                "status": "ok",
                "backend_mode": self.settings.backend_mode,
                "checks": {"app": {"status": "ok"}},
            }

        checks = {
            "postgres": self._run_check(self._check_postgres),
            "redis": self._run_check(self._check_redis),
            "s3": self._run_check(self._check_s3),
            "queue": self._run_check(self._check_queue),
        }
        overall = "ok" if all(item["status"] == "ok" for item in checks.values()) else "error"
        return {"status": overall, "backend_mode": self.settings.backend_mode, "checks": checks}

    def _run_check(self, fn: Callable[[], None]) -> dict:
        try:
            fn()
            return {"status": "ok"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    def _check_postgres(self) -> None:
        with get_engine().connect() as connection:
            connection.execute(text("select 1"))

    def _check_redis(self) -> None:
        client = redis.Redis.from_url(self.settings.redis_url, decode_responses=True)
        client.ping()

    def _check_s3(self) -> None:
        client = boto3.client(
            "s3",
            region_name=self.settings.aws_region,
            endpoint_url=self.settings.s3_endpoint_url,
            aws_access_key_id=self.settings.aws_access_key_id or None,
            aws_secret_access_key=self.settings.aws_secret_access_key or None,
        )
        client.head_bucket(Bucket=self.settings.s3_bucket)

    def _check_queue(self) -> None:
        client = boto3.client(
            "sqs",
            region_name=self.settings.aws_region,
            endpoint_url=self.settings.aws_endpoint_url,
            aws_access_key_id=self.settings.aws_access_key_id or None,
            aws_secret_access_key=self.settings.aws_secret_access_key or None,
        )
        client.get_queue_attributes(
            QueueUrl=self.settings.audit_queue_url,
            AttributeNames=["QueueArn"],
        )
