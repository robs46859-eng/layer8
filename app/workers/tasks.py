import argparse
import json
import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime

import boto3

from app.core.config import get_settings
from app.db.models import RequestAudit
from app.db.session import get_session_factory
from app.schemas.inference import InferenceResponse

logger = logging.getLogger(__name__)


@dataclass
class AuditTask:
    request_id: str
    tenant_id: str
    response: InferenceResponse
    receipt_handle: str
    queue_url: str


class AuditWorker:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.session_factory = get_session_factory()
        self.sqs = boto3.client(
            "sqs",
            region_name=self.settings.aws_region,
            endpoint_url=self.settings.aws_endpoint_url,
            aws_access_key_id=self.settings.aws_access_key_id or None,
            aws_secret_access_key=self.settings.aws_secret_access_key or None,
        )
        self.s3 = boto3.client(
            "s3",
            region_name=self.settings.aws_region,
            endpoint_url=self.settings.s3_endpoint_url,
            aws_access_key_id=self.settings.aws_access_key_id or None,
            aws_secret_access_key=self.settings.aws_secret_access_key or None,
        )

    def run(self, once: bool = False) -> None:
        while True:
            processed = self.poll_once()
            if once:
                return
            if processed == 0:
                time.sleep(self.settings.worker_poll_seconds)

    def poll_once(self) -> int:
        response = self.sqs.receive_message(
            QueueUrl=self.settings.audit_queue_url,
            MaxNumberOfMessages=self.settings.worker_batch_size,
            WaitTimeSeconds=1,
            MessageAttributeNames=["All"],
        )
        messages = response.get("Messages", [])
        for message in messages:
            task = self._parse_message(message)
            self.persist_audit_blob(task)
            self.sqs.delete_message(QueueUrl=task.queue_url, ReceiptHandle=task.receipt_handle)
            logger.info({"event": "audit_task_processed", "request_id": task.request_id})
        return len(messages)

    def _parse_message(self, message: dict) -> AuditTask:
        payload = json.loads(message["Body"])
        attributes = message.get("MessageAttributes", {})
        request_id = attributes.get("request_id", {}).get("StringValue") or payload["request_id"]
        tenant_id = attributes.get("tenant_id", {}).get("StringValue") or payload["tenant_id"]
        return AuditTask(
            request_id=request_id,
            tenant_id=tenant_id,
            response=InferenceResponse(**payload),
            receipt_handle=message["ReceiptHandle"],
            queue_url=self.settings.audit_queue_url,
        )

    def persist_audit_blob(self, task: AuditTask) -> None:
        object_key = f"audit/{task.tenant_id}/{task.request_id}.json"
        body = task.response.model_dump_json().encode("utf-8")
        self.s3.put_object(
            Bucket=self.settings.s3_bucket,
            Key=object_key,
            Body=body,
            ContentType="application/json",
        )
        audit_blob_uri = f"s3://{self.settings.s3_bucket}/{object_key}"
        with self.session_factory() as session:
            audit_row = session.query(RequestAudit).filter_by(request_id=task.request_id).one_or_none()
            if audit_row is None:
                raise RuntimeError(f"missing audit row for request_id={task.request_id}")
            metadata = dict(audit_row.metadata_json or {})
            metadata["worker_processed_at"] = datetime.now(UTC).isoformat()
            audit_row.audit_blob_uri = audit_blob_uri
            audit_row.metadata_json = metadata
            session.commit()


def process_provider_fallback(request_id: str) -> None:
    """Placeholder for queue-based fallback handling outside the request thread."""
    logger.info({"event": "provider_fallback_placeholder", "request_id": request_id})


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the audit queue worker.")
    parser.add_argument("--once", action="store_true", help="Process at most one batch and exit.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    worker = AuditWorker()
    worker.run(once=args.once)


if __name__ == "__main__":
    main()
