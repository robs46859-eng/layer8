from collections.abc import Callable

import boto3
import redis
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient
from azure.storage.blob import BlobServiceClient
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
            "audit_storage": self._run_check(self._check_audit_storage),
            "queue": self._run_check(self._check_queue),
        }
        overall = "ok" if all(item["status"] == "ok" for item in checks.values()) else "error"
        return {"status": overall, "backend_mode": self.settings.backend_mode, "checks": checks}

    def _run_check(self, fn: Callable[[], None]) -> dict:
        try:
            fn()
            return {"status": "ok"}
        except Exception as exc:  # noqa: BLE001 - readiness must report any dependency failure
            return {"status": "error", "detail": str(exc)}

    def _check_postgres(self) -> None:
        with get_engine().connect() as connection:
            connection.execute(text("select 1"))

    def _check_redis(self) -> None:
        client = redis.Redis.from_url(self.settings.redis_url, decode_responses=True)
        client.ping()

    def _check_audit_storage(self) -> None:
        if self.settings.audit_backend == "azure":
            client = BlobServiceClient(
                account_url=self.settings.azure_blob_account_url,
                credential=DefaultAzureCredential(),
            )
            client.get_container_client(self.settings.azure_blob_container).get_container_properties()
            return
        client = boto3.client(
            "s3",
            region_name=self.settings.aws_region,
            endpoint_url=self.settings.s3_endpoint_url,
            aws_access_key_id=self.settings.aws_access_key_id or None,
            aws_secret_access_key=self.settings.aws_secret_access_key or None,
        )
        client.head_bucket(Bucket=self.settings.s3_bucket)

    def _check_queue(self) -> None:
        if self.settings.audit_backend == "azure":
            client = ServiceBusClient(
                fully_qualified_namespace=self.settings.azure_service_bus_namespace,
                credential=DefaultAzureCredential(),
            )
            with client.get_queue_sender(queue_name=self.settings.azure_service_bus_queue):
                return
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
