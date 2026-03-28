from typing import Protocol

from app.schemas.inference import InferenceResponse
from app.services.context import RequestContext


class BeforePlugin(Protocol):
    name: str
    blocking: bool

    async def run(self, context: RequestContext) -> RequestContext: ...


class AfterPlugin(Protocol):
    name: str
    blocking: bool

    async def run(self, context: RequestContext, response: InferenceResponse) -> InferenceResponse: ...


class PromptMetadataPlugin:
    name = "prompt-metadata"
    blocking = True

    async def run(self, context: RequestContext) -> RequestContext:
        context.payload.metadata.setdefault("request_id", context.request_id)
        return context


class AuditTagPlugin:
    name = "audit-tag"
    blocking = False

    async def run(self, context: RequestContext, response: InferenceResponse) -> InferenceResponse:
        response.audit_reference = f"audit://{context.request_id}"
        return response
