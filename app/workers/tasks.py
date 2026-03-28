from dataclasses import dataclass


@dataclass
class AuditTask:
    request_id: str
    audit_blob_uri: str
    tenant_id: str


async def persist_audit_blob(task: AuditTask) -> None:
    """Placeholder for S3 archival and PostgreSQL audit reference updates."""
    return None


async def process_provider_fallback(request_id: str) -> None:
    """Placeholder for queue-based fallback handling outside the request thread."""
    return None
