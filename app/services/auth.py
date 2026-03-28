from dataclasses import dataclass
from typing import Protocol

from app.core.config import Settings
from app.core.security import hash_api_secret, split_api_key, verify_api_secret
from app.db.models import APIKey, Tenant
from app.db.session import get_session_factory
from app.services.context import RequestContext


@dataclass
class APIKeyRecord:
    key_id: str
    tenant_id: str
    prefix: str
    secret_hash: str
    scopes: set[str]
    allowed_models: set[str]
    active: bool = True
    key_status: str = "active"
    tenant_status: str = "active"


class APIKeyStore(Protocol):
    async def get_by_prefix(self, prefix: str) -> APIKeyRecord | None: ...


class InMemoryAPIKeyStore:
    def __init__(self, records: dict[str, APIKeyRecord]) -> None:
        self.records = records

    @classmethod
    def from_settings(cls, settings: Settings) -> "InMemoryAPIKeyStore":
        record = APIKeyRecord(
            key_id="key_dev_001",
            tenant_id="tenant_dev",
            prefix=settings.dev_api_key_prefix,
            secret_hash=hash_api_secret(settings.dev_api_key_prefix, settings.dev_api_key_secret),
            scopes={"inference:invoke"},
            allowed_models={"gpt-4.1-mini", "gpt-4.1", "mock-echo"},
            key_status="active",
            tenant_status="active",
        )
        return cls(records={record.prefix: record})

    async def get_by_prefix(self, prefix: str) -> APIKeyRecord | None:
        return self.records.get(prefix)


class PostgresAPIKeyStore:
    def __init__(self) -> None:
        self.session_factory = get_session_factory()

    async def get_by_prefix(self, prefix: str) -> APIKeyRecord | None:
        with self.session_factory() as session:
            row = (
                session.query(APIKey, Tenant)
                .join(Tenant, APIKey.tenant_id == Tenant.id)
                .filter(APIKey.prefix == prefix)
                .one_or_none()
            )
            if row is None:
                return None
            api_key, tenant = row
            return APIKeyRecord(
                key_id=api_key.id,
                tenant_id=tenant.id,
                prefix=api_key.prefix,
                secret_hash=api_key.secret_hash,
                scopes=set(api_key.scopes or []),
                allowed_models=set(api_key.allowed_models or []),
                active=api_key.status == "active" and tenant.status == "active",
                key_status=api_key.status,
                tenant_status=tenant.status,
            )


class AuthService:
    def __init__(self, store: APIKeyStore) -> None:
        self.store = store

    async def authenticate(self, context: RequestContext) -> RequestContext:
        context.stage_trace.append("auth")
        prefix, secret = split_api_key(context.presented_api_key)
        record = await self.store.get_by_prefix(prefix)
        if record is None:
            raise PermissionError("unknown or inactive api key")
        if record.tenant_status != "active":
            raise PermissionError("tenant is inactive")
        if record.key_status != "active" or not record.active:
            raise PermissionError("api key is inactive")
        if not verify_api_secret(record.prefix, secret, record.secret_hash):
            raise PermissionError("invalid api key")
        context.tenant_id = record.tenant_id
        context.api_key_id = record.key_id
        context.api_key_scopes = set(record.scopes)
        context.allowed_models = set(record.allowed_models)
        return context
