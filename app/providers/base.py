from typing import Protocol

from app.schemas.inference import InferenceResponse, Usage
from app.services.context import RequestContext


class ProviderAdapter(Protocol):
    name: str

    async def infer(self, context: RequestContext) -> InferenceResponse: ...


class ProviderRegistry:
    def __init__(self, providers: dict[str, ProviderAdapter]) -> None:
        self.providers = providers

    def get(self, provider_name: str) -> ProviderAdapter:
        provider = self.providers.get(provider_name)
        if provider is None:
            raise RuntimeError(f"provider {provider_name} is not registered")
        return provider


class EchoProvider:
    name = "mock"

    async def infer(self, context: RequestContext) -> InferenceResponse:
        prompt = context.payload.messages[-1].content if context.payload.messages else ""
        return InferenceResponse(
            request_id=context.request_id,
            tenant_id=context.tenant_id or "unknown",
            provider=self.name,
            model=context.payload.model,
            output_text=f"echo:{prompt}",
            usage=Usage(prompt_tokens=len(prompt.split()), completion_tokens=1, total_tokens=1),
        )
