from dataclasses import dataclass, field
from typing import Any

from app.core.security import generate_request_id, generate_trace_id
from app.schemas.inference import InferenceRequest


@dataclass
class RequestContext:
    request_id: str
    trace_id: str
    payload: InferenceRequest
    presented_api_key: str
    idempotency_key: str | None
    client_host: str | None
    tenant_id: str | None = None
    api_key_id: str | None = None
    api_key_scopes: set[str] = field(default_factory=set)
    allowed_models: set[str] = field(default_factory=set)
    policy_snapshot: dict[str, Any] = field(default_factory=dict)
    selected_provider: str | None = None
    plugin_bindings: list[str] = field(default_factory=list)
    canonical_cache_key: str | None = None
    stage_trace: list[str] = field(default_factory=list)

    @classmethod
    def from_request(
        cls,
        payload: InferenceRequest,
        presented_api_key: str,
        idempotency_key: str | None,
        client_host: str | None,
    ) -> "RequestContext":
        return cls(
            request_id=generate_request_id(),
            trace_id=generate_trace_id(),
            payload=payload,
            presented_api_key=presented_api_key,
            idempotency_key=idempotency_key,
            client_host=client_host,
        )
