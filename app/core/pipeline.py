from app.core.config import get_settings
from app.providers.base import ProviderRegistry
from app.providers.openai import MockProvider, OpenAIChatProvider
from app.services.audit import AuditService
from app.services.auth import AuthService, InMemoryAPIKeyStore, PostgresAPIKeyStore
from app.services.cache import CacheService, InMemoryCacheStore, RedisCacheStore
from app.services.context import RequestContext
from app.services.plugin_runtime import PluginRuntime
from app.services.policy import PolicyService
from app.services.rate_limit import InMemoryRateLimitStore, RateLimitService, RedisRateLimitStore
from app.services.routing import RoutingService


class InferencePipeline:
    def __init__(
        self,
        auth_service: AuthService,
        rate_limit_service: RateLimitService,
        plugin_runtime: PluginRuntime,
        cache_service: CacheService,
        routing_service: RoutingService,
        audit_service: AuditService,
        policy_service: PolicyService,
    ) -> None:
        self.auth_service = auth_service
        self.rate_limit_service = rate_limit_service
        self.plugin_runtime = plugin_runtime
        self.cache_service = cache_service
        self.routing_service = routing_service
        self.audit_service = audit_service
        self.policy_service = policy_service

    async def execute(
        self,
        payload,
        presented_api_key: str,
        idempotency_key: str | None,
        client_host: str | None,
    ):
        context = RequestContext.from_request(
            payload=payload,
            presented_api_key=presented_api_key,
            idempotency_key=idempotency_key,
            client_host=client_host,
        )

        context = await self.auth_service.authenticate(context)
        await self.policy_service.evaluate(context)
        await self.rate_limit_service.enforce(context)
        context = await self.plugin_runtime.run_before(context)

        cached = await self.cache_service.get(context)
        if cached is not None:
            cached.stage_trace = [*context.stage_trace, "logging", "return"]
            context.stage_trace.append("return")
            await self.audit_service.record(context, cached, cache_hit=True)
            return cached

        response = await self.routing_service.route(context)
        await self.cache_service.put(context, response)
        response = await self.plugin_runtime.run_after(context, response)
        await self.audit_service.record(context, response, cache_hit=False)
        context.stage_trace.append("return")
        response.stage_trace = context.stage_trace
        return response


def build_pipeline() -> InferencePipeline:
    settings = get_settings()
    provider_registry = ProviderRegistry(
        {
            "mock": MockProvider(),
            "openai": OpenAIChatProvider(settings),
        }
    )
    if settings.backend_mode == "self_hosted":
        auth_store = PostgresAPIKeyStore()
        rate_limit_store = RedisRateLimitStore(
            redis_url=settings.redis_url,
            limit_per_minute=settings.rate_limit_requests_per_minute,
        )
        cache_store = RedisCacheStore(settings)
    else:
        auth_store = InMemoryAPIKeyStore.from_settings(settings)
        rate_limit_store = InMemoryRateLimitStore(
            limit_per_minute=settings.rate_limit_requests_per_minute
        )
        cache_store = InMemoryCacheStore(ttl_seconds=settings.cache_ttl_seconds)
    return InferencePipeline(
        auth_service=AuthService(auth_store),
        rate_limit_service=RateLimitService(store=rate_limit_store),
        plugin_runtime=PluginRuntime(timeout_ms=settings.plugin_timeout_ms),
        cache_service=CacheService(store=cache_store),
        routing_service=RoutingService(
            provider_registry=provider_registry,
            default_provider=settings.default_provider,
        ),
        audit_service=AuditService(settings),
        policy_service=PolicyService(),
    )
