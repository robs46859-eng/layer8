from app.services.cache import CacheService, InMemoryCacheStore
from app.services.context import RequestContext
from app.core.pipeline import build_pipeline
from app.schemas.inference import InferenceRequest, Message


async def _invoke(pipeline, tenant_key: str, plugin_set: list[str] | None = None):
    return await pipeline.execute(
        payload=InferenceRequest(
            model="gpt-4.1-mini",
            messages=[Message(role="user", content="hello")],
            plugin_set=plugin_set or [],
        ),
        presented_api_key=tenant_key,
        idempotency_key=None,
        client_host="127.0.0.1",
    )


def test_pipeline_stage_order():
    import asyncio

    pipeline = build_pipeline()
    response = asyncio.run(_invoke(pipeline, "ak_live_demo.change-me-now", ["prompt-metadata"]))
    assert response.stage_trace == [
        "auth",
        "rate_limit",
        "plugins_before",
        "cache_check",
        "provider_routing",
        "cache_write",
        "plugins_after",
        "logging",
        "return",
    ]


def test_cache_is_tenant_scoped():
    import asyncio

    pipeline = build_pipeline()
    first = asyncio.run(_invoke(pipeline, "ak_live_demo.change-me-now"))
    second = asyncio.run(_invoke(pipeline, "ak_live_demo.change-me-now"))
    assert first.cached is False
    assert second.cached is True
    assert second.stage_trace == [
        "auth",
        "rate_limit",
        "plugins_before",
        "cache_check",
        "logging",
        "return",
    ]


def test_cache_key_partitions_tenants():
    cache = CacheService(store=InMemoryCacheStore(ttl_seconds=300))
    payload = InferenceRequest(model="gpt-4.1-mini", messages=[Message(role="user", content="hello")])
    first = RequestContext.from_request(
        payload=payload,
        presented_api_key="ak_live_demo.change-me-now",
        idempotency_key=None,
        client_host="127.0.0.1",
    )
    first.tenant_id = "tenant_a"
    second = RequestContext.from_request(
        payload=payload,
        presented_api_key="ak_live_other.change-me-now",
        idempotency_key=None,
        client_host="127.0.0.1",
    )
    second.tenant_id = "tenant_b"
    assert cache._build_key(first) != cache._build_key(second)


def test_invalid_api_key_fails_closed():
    import asyncio

    pipeline = build_pipeline()
    try:
        asyncio.run(_invoke(pipeline, "ak_live_demo.bad-secret"))
    except PermissionError as exc:
        assert "invalid api key" in str(exc)
    else:
        raise AssertionError("expected permission error")
