import hashlib
from contextlib import suppress
from dataclasses import dataclass
from typing import Protocol

import boto3
import orjson
import redis

from app.core.config import Settings
from app.db.models import CacheManifest
from app.db.session import get_session_factory
from app.schemas.inference import InferenceResponse
from app.services.context import RequestContext


@dataclass
class CacheEntry:
    response: InferenceResponse


class CacheStore(Protocol):
    async def get(self, key: str) -> InferenceResponse | None: ...

    async def put(self, key: str, response: InferenceResponse) -> None: ...


class InMemoryCacheStore:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self.entries: dict[str, CacheEntry] = {}

    async def get(self, key: str) -> InferenceResponse | None:
        entry = self.entries.get(key)
        if entry is None:
            return None
        return entry.response.model_copy(update={"cached": True, "stage_trace": []})

    async def put(self, key: str, response: InferenceResponse) -> None:
        self.entries[key] = CacheEntry(response=response)


class RedisCacheStore:
    def __init__(self, settings: Settings) -> None:
        self.client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        self.ttl_seconds = settings.cache_ttl_seconds
        self.threshold = settings.cache_s3_threshold_bytes
        self.bucket = settings.s3_bucket
        self.s3 = boto3.client(
            "s3",
            region_name=settings.aws_region,
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
        self.session_factory = get_session_factory()

    async def get(self, key: str) -> InferenceResponse | None:
        payload = self.client.get(key)
        if payload is None:
            return None
        data = orjson.loads(payload)
        storage_uri = data.get("storage_uri")
        if storage_uri:
            bucket, object_key = storage_uri.removeprefix("s3://").split("/", 1)
            obj = self.s3.get_object(Bucket=bucket, Key=object_key)
            body = obj["Body"].read()
            response_data = orjson.loads(body)
        else:
            response_data = data["response"]
        return InferenceResponse(**response_data).model_copy(update={"cached": True, "stage_trace": []})

    async def put(self, key: str, response: InferenceResponse) -> None:
        payload = response.model_dump()
        raw = orjson.dumps(payload)
        storage_uri = None
        if len(raw) > self.threshold:
            object_key = f"cache/{key}.json"
            self.s3.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=raw,
                ContentType="application/json",
            )
            storage_uri = f"s3://{self.bucket}/{object_key}"
            cache_value = {"storage_uri": storage_uri}
        else:
            cache_value = {"response": payload}
        self.client.setex(key, self.ttl_seconds, orjson.dumps(cache_value).decode("utf-8"))
        with self.session_factory() as session:
            manifest = CacheManifest(
                tenant_id=response.tenant_id,
                cache_key=key,
                storage_uri=storage_uri,
                content_sha256=hashlib.sha256(raw).hexdigest(),
                metadata_json={"provider": response.provider, "model": response.model},
            )
            with suppress(Exception):
                session.merge(manifest)
                session.commit()


class CacheService:
    def __init__(self, store: CacheStore) -> None:
        self.store = store

    async def get(self, context: RequestContext) -> InferenceResponse | None:
        context.stage_trace.append("cache_check")
        key = self._build_key(context)
        context.canonical_cache_key = key
        return await self.store.get(key)

    async def put(self, context: RequestContext, response: InferenceResponse) -> None:
        context.stage_trace.append("cache_write")
        await self.store.put(context.canonical_cache_key or self._build_key(context), response)

    def _build_key(self, context: RequestContext) -> str:
        canonical = {
            "tenant_id": context.tenant_id,
            "model": context.payload.model,
            "messages": [message.model_dump() for message in context.payload.messages],
            "temperature": context.payload.temperature,
            "max_tokens": context.payload.max_tokens,
            "plugin_set": sorted(context.payload.plugin_set),
            "provider_hint": context.payload.provider_hint,
        }
        digest = hashlib.sha256(orjson.dumps(canonical, option=orjson.OPT_SORT_KEYS)).hexdigest()
        return f"{context.tenant_id}:{digest}"
