import logging

import boto3

from app.core.config import Settings
from app.db.models import RequestAudit
from app.db.session import get_session_factory
from app.schemas.inference import InferenceResponse
from app.services.context import RequestContext

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session_factory = get_session_factory() if settings.backend_mode == "self_hosted" else None
        self.sqs = (
            boto3.client(
                "sqs",
                region_name=settings.aws_region,
                endpoint_url=settings.aws_endpoint_url,
                aws_access_key_id=settings.aws_access_key_id or None,
                aws_secret_access_key=settings.aws_secret_access_key or None,
            )
            if settings.backend_mode == "self_hosted"
            else None
        )

    async def record(
        self, context: RequestContext, response: InferenceResponse, cache_hit: bool
    ) -> None:
        context.stage_trace.append("logging")
        audit_blob_uri = response.audit_reference
        if self.session_factory is not None:
            with self.session_factory() as session:
                session.merge(
                    RequestAudit(
                        request_id=context.request_id,
                        tenant_id=context.tenant_id or "unknown",
                        api_key_id=context.api_key_id or "unknown",
                        provider_name=response.provider,
                        model_name=response.model,
                        cache_hit=cache_hit,
                        audit_blob_uri=audit_blob_uri,
                        metadata_json={
                            "trace_id": context.trace_id,
                            "plugin_bindings": context.plugin_bindings,
                            "selected_provider": context.selected_provider,
                        },
                    )
                )
                session.commit()
        if self.sqs is not None and self.settings.audit_queue_url:
            self.sqs.send_message(
                QueueUrl=self.settings.audit_queue_url,
                MessageBody=response.model_dump_json(),
                MessageAttributes={
                    "request_id": {"DataType": "String", "StringValue": context.request_id},
                    "tenant_id": {
                        "DataType": "String",
                        "StringValue": context.tenant_id or "unknown",
                    },
                },
            )
        logger.info(
            {
                "event": "proxy_request_completed",
                "request_id": context.request_id,
                "trace_id": context.trace_id,
                "tenant_id": context.tenant_id,
                "api_key_id": context.api_key_id,
                "provider": response.provider,
                "model": response.model,
                "cache_hit": cache_hit,
                "plugin_bindings": context.plugin_bindings,
                "audit_queue_url": self.settings.audit_queue_url,
            }
        )
