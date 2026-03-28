from datetime import UTC, datetime
import secrets
import uuid

from sqlalchemy.orm import Session

from app.core.security import hash_api_secret
from app.db.models import APIKey, Tenant


class APIKeyAdminService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_api_keys(self, tenant_id: str) -> list[APIKey]:
        self._require_tenant(tenant_id)
        return (
            self.session.query(APIKey)
            .filter(APIKey.tenant_id == tenant_id)
            .order_by(APIKey.created_at.asc())
            .all()
        )

    def create_api_key(
        self, tenant_id: str, scopes: list[str], allowed_models: list[str]
    ) -> tuple[APIKey, str]:
        self._require_tenant(tenant_id)
        now = datetime.now(UTC).replace(tzinfo=None)
        prefix = f"ak_live_{secrets.token_hex(8)}"
        secret = secrets.token_hex(24)
        api_key = APIKey(
            id=f"key_{uuid.uuid4().hex}",
            tenant_id=tenant_id,
            prefix=prefix,
            secret_hash=hash_api_secret(prefix, secret),
            scopes=sorted(set(scopes)),
            allowed_models=sorted(set(allowed_models)),
            status="active",
            created_at=now,
            updated_at=now,
            revoked_at=None,
        )
        self.session.add(api_key)
        self.session.commit()
        self.session.refresh(api_key)
        return api_key, f"{prefix}.{secret}"

    def revoke_api_key(self, key_id: str) -> APIKey:
        api_key = self._get_api_key(key_id)
        if api_key.status != "revoked":
            api_key.status = "revoked"
            api_key.revoked_at = datetime.now(UTC).replace(tzinfo=None)
            api_key.updated_at = api_key.revoked_at
            self.session.add(api_key)
            self.session.commit()
            self.session.refresh(api_key)
        return api_key

    def rotate_api_key(self, key_id: str) -> tuple[APIKey, str]:
        current_key = self._get_api_key(key_id)
        new_key, raw_key = self.create_api_key(
            current_key.tenant_id,
            list(current_key.scopes or []),
            list(current_key.allowed_models or []),
        )
        self.revoke_api_key(current_key.id)
        return new_key, raw_key

    def _require_tenant(self, tenant_id: str) -> Tenant:
        tenant = self.session.get(Tenant, tenant_id)
        if tenant is None:
            raise ValueError("tenant not found")
        return tenant

    def _get_api_key(self, key_id: str) -> APIKey:
        api_key = self.session.get(APIKey, key_id)
        if api_key is None:
            raise ValueError("api key not found")
        return api_key
