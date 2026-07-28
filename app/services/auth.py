from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.core.config import Settings
from app.core.security import hash_api_secret, split_api_key, verify_api_secret
from app.db.models import APIKey, BillingAccount, Tenant
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
    billing_status: str = "inactive"
    billing_entitlements: set[str] | None = None
    payment_grace_ends_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.billing_entitlements is None:
            self.billing_entitlements = set()


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
            scopes={"inference:invoke", "spatial:invoke"},
            allowed_models={"gpt-4.1-mini", "gpt-4.1", "mock-echo"},
            key_status="active",
            tenant_status="active",
            billing_status="active",
            billing_entitlements={"api_access", "spatial_intelligence"},
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
                session.query(APIKey, Tenant, BillingAccount)
                .join(Tenant, APIKey.tenant_id == Tenant.id)
                .outerjoin(BillingAccount, BillingAccount.tenant_id == Tenant.id)
                .filter(APIKey.prefix == prefix)
                .one_or_none()
            )
            if row is None:
                return None
            api_key, tenant, billing_account = row
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
                billing_status=(
                    billing_account.subscription_status
                    if billing_account is not None
                    else "inactive"
                ),
                billing_entitlements=(
                    set(billing_account.entitlements or [])
                    if billing_account is not None
                    else set()
                ),
                payment_grace_ends_at=(
                    billing_account.payment_grace_ends_at
                    if billing_account is not None
                    else None
                ),
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
        context.billing_status = record.billing_status
        context.billing_entitlements = set(record.billing_entitlements or set())
        context.payment_grace_ends_at = record.payment_grace_ends_at
        return context
