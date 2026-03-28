from app.providers.base import ProviderRegistry
from app.services.context import RequestContext


class RoutingService:
    def __init__(self, provider_registry: ProviderRegistry, default_provider: str) -> None:
        self.provider_registry = provider_registry
        self.default_provider = default_provider

    async def route(self, context: RequestContext):
        context.stage_trace.append("provider_routing")
        provider_name = context.payload.provider_hint or self.default_provider
        context.selected_provider = provider_name
        provider = self.provider_registry.get(provider_name)
        return await provider.infer(context)
