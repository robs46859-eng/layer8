"""Default-off Layer8 Adaptive policy boundary for nonclinical VirtuaPet previews.

Never invokes providers, creates tenants, changes subscriptions, or accepts
platform-admin/internal-spatial bypasses. Grants are short-lived and context-bound.
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from uuid import UUID, uuid4

import jwt
import redis
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clerk import clerk_organization_id
from app.core.config import Settings, get_settings
from app.core.security import split_api_key, verify_api_secret
from app.db.models import Tenant
from app.schemas.virtuapet import LinkProofRequest, PolicyRequest
from app.services.auth import APIKeyRecord, APIKeyStore, PostgresAPIKeyStore
from app.services.entitlements import has_billing_access
from app.services.rate_limit import InMemoryRateLimitStore

logger = logging.getLogger(__name__)
LINK_PROTOCOL = "virtuapet.layer8.link.v1"
POLICY_PROTOCOL = "virtuapet.layer8.policy.v1"
LINK_TYPE = "vp-layer8-link+jwt"
POLICY_TYPE = "vp-layer8-policy+jwt"
POLICY_VERSION = "virtuapet-nonclinical-v1"
LINK_FIELDS = {
    "iss", "aud", "sub", "iat", "exp", "jti", "protocol", "tenantId", "challengeId", "nonce",
    "providerSubject", "providerTenantId", "providerOrganizationId",
}


def integration_error(code: str, status: int = 503) -> HTTPException:
    return HTTPException(status_code=status, detail=code, headers={"Cache-Control": "no-store"})


def _canonical(value: object, limit: int = 256) -> bool:
    return (isinstance(value, str) and 0 < len(value) <= limit and value == value.strip()
            and all(ord(char) >= 32 and ord(char) != 127 for char in value))


def _uuid(value: object) -> bool:
    try:
        return isinstance(value, str) and str(UUID(value)) == value
    except ValueError:
        return False


def bearer_token(authorization: str | None) -> str:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token or len(token) > 16384 or any(
        char.isspace() for char in token
    ):
        raise integration_error("virtuapet_auth_required", 401)
    return token


@dataclass(frozen=True)
class ClerkIdentity:
    subject: str
    organization_id: str
    tenant_id: str
    expires_at: int


class IntegrationLimiter:
    """Per-tenant limit; Redis Lua keeps increment+expiry atomic across replicas."""

    def __init__(self, settings: Settings) -> None:
        self.limit = settings.virtuapet_rate_limit_per_minute
        self.memory = None
        self.client = None
        self.requests: dict[str, float] = {}
        if settings.environment.lower() in {"dev", "development", "test"} and (
            settings.backend_mode == "memory"
        ):
            self.memory = InMemoryRateLimitStore(self.limit)
        else:
            self.client = redis.Redis.from_url(
                settings.redis_url, socket_connect_timeout=2, socket_timeout=2,
                decode_responses=True,
            )

    async def enforce(self, tenant_id: str, operation: str) -> None:
        try:
            if self.memory:
                await self.memory.increment(tenant_id, "virtuapet", operation)
                return
            key = "virtuapet:rate:" + hashlib.sha256(
                f"{tenant_id}:{operation}".encode()
            ).hexdigest()
            count = self.client.eval(
                "local n=redis.call('INCR',KEYS[1]); "
                "if n==1 then redis.call('EXPIRE',KEYS[1],60) end; return n", 1, key,
            )
            if int(count) > self.limit:
                raise RuntimeError("rate limit exceeded")
        except redis.RedisError as exc:
            raise integration_error("virtuapet_rate_limit_unavailable") from exc
        except RuntimeError as exc:
            raise integration_error("virtuapet_rate_limited", 429) from exc

    async def reserve_request(self, tenant_id: str, request_id: str) -> None:
        """A retry needs a fresh request ID; a captured policy response cannot be reused."""
        key = "virtuapet:request:" + hashlib.sha256(
            f"{tenant_id}:{request_id}".encode()
        ).hexdigest()
        if self.memory:
            now = time.time()
            self.requests = {k: expiry for k, expiry in self.requests.items() if expiry > now}
            if key in self.requests:
                raise integration_error("virtuapet_request_replayed", 409)
            self.requests[key] = now + 300
            return
        try:
            if not self.client.set(key, "1", ex=300, nx=True):
                raise integration_error("virtuapet_request_replayed", 409)
        except redis.RedisError as exc:
            raise integration_error("virtuapet_replay_store_unavailable") from exc


class VirtuaPetService:
    def __init__(self, settings: Settings, *, key_store: APIKeyStore | None = None) -> None:
        self.settings = settings
        if not settings.virtuapet_integration_enabled:
            raise integration_error("virtuapet_disabled")
        if settings.environment.lower() not in {"dev", "development", "test"} and (
            settings.backend_mode != "self_hosted"
            or not settings.database_url.startswith("postgresql+")
        ):
            raise integration_error("virtuapet_persistent_backend_required")
        self.issuer = settings.virtuapet_policy_issuer
        self.audience = settings.virtuapet_policy_audience
        self.link_audience = settings.virtuapet_link_audience
        self.kid = settings.virtuapet_signing_key_id
        if not all(_canonical(v) for v in (self.issuer, self.audience, self.link_audience, self.kid)):
            raise integration_error("virtuapet_unconfigured")
        if self.audience == self.link_audience:
            raise integration_error("virtuapet_unconfigured")
        try:
            self.key = serialization.load_pem_private_key(
                settings.virtuapet_signing_private_key.replace("\\n", "\n").encode(), password=None,
            )
            if not isinstance(self.key, ec.EllipticCurvePrivateKey) or not isinstance(
                self.key.curve, ec.SECP256R1
            ):
                raise TypeError("P-256 required")
            self.tenant_map = json.loads(settings.virtuapet_tenant_map_json)
            if not isinstance(self.tenant_map, dict) or not self.tenant_map or any(
                not _uuid(k) or not _canonical(v, 64) for k, v in self.tenant_map.items()
            ):
                raise ValueError("invalid tenant map")
        except (ValueError, TypeError) as exc:
            raise integration_error("virtuapet_unconfigured") from exc
        self.public_key = self.key.public_key()
        # Even development uses stored hashed API keys, never the broad demo key.
        self.key_store = key_store or PostgresAPIKeyStore()
        self.limiter = IntegrationLimiter(settings)

    def authenticate_clerk(self, session: Session, authorization: str | None) -> ClerkIdentity:
        settings = self.settings
        parties = {p.strip() for p in settings.clerk_authorized_parties.split(",") if p.strip()}
        if not settings.clerk_jwt_key or not settings.clerk_issuer or not parties or "*" in parties:
            raise integration_error("virtuapet_clerk_unconfigured")
        token = bearer_token(authorization)
        try:
            claims = jwt.decode(
                token, settings.clerk_jwt_key.replace("\\n", "\n"), algorithms=["RS256"],
                issuer=settings.clerk_issuer,
                options={"verify_aud": False, "require": ["exp", "iat", "nbf", "iss", "sub", "azp"]},
            )
        except jwt.InvalidTokenError as exc:
            raise integration_error("virtuapet_invalid_clerk_session", 401) from exc
        try:
            organization_id = clerk_organization_id(claims)
        except ValueError as exc:
            raise integration_error("virtuapet_invalid_clerk_identity", 403) from exc
        if (not _canonical(claims.get("azp")) or claims.get("azp") not in parties
                or not _canonical(claims.get("sub"))
                or organization_id is None
                or any(not isinstance(claims.get(k), int) or isinstance(claims.get(k), bool)
                       for k in ("exp", "iat", "nbf"))):
            raise integration_error("virtuapet_invalid_clerk_identity", 403)
        tenant = session.scalar(select(Tenant).where(
            Tenant.clerk_organization_id == organization_id
        ))
        if tenant is None or tenant.status != "active":
            raise integration_error("virtuapet_inactive_organization", 403)
        return ClerkIdentity(claims["sub"], organization_id, tenant.id, claims["exp"])

    async def link_proof(self, request: LinkProofRequest, identity: ClerkIdentity) -> str:
        if self.tenant_map.get(str(request.tenantId)) != identity.tenant_id:
            raise integration_error("virtuapet_tenant_mismatch", 403)
        await self.limiter.enforce(identity.tenant_id, "link-proof")
        now = int(time.time())
        expires = min(now + 300, identity.expires_at)
        if expires <= now:
            raise integration_error("virtuapet_expired_identity", 401)
        claims = {
            "iss": self.issuer, "aud": self.link_audience, "sub": str(request.subject),
            "iat": now, "exp": expires, "jti": str(uuid4()), "protocol": LINK_PROTOCOL,
            "tenantId": str(request.tenantId), "challengeId": str(request.challengeId),
            "nonce": str(request.nonce), "providerSubject": identity.subject,
            "providerTenantId": identity.tenant_id, "providerOrganizationId": identity.organization_id,
        }
        return jwt.encode(claims, self.key, algorithm="ES256", headers={"kid": self.kid, "typ": LINK_TYPE})

    async def authenticate_key(self, authorization: str | None) -> APIKeyRecord:
        try:
            prefix, secret = split_api_key(bearer_token(authorization))
        except PermissionError as exc:
            raise integration_error("virtuapet_invalid_service_key", 401) from exc
        try:
            record = await self.key_store.get_by_prefix(prefix)
        except Exception as exc:
            raise integration_error("virtuapet_key_store_unavailable") from exc
        if (record is None or not record.active or record.key_status != "active"
                or record.tenant_status != "active"
                or not verify_api_secret(record.prefix, secret, record.secret_hash)):
            raise integration_error("virtuapet_invalid_service_key", 401)
        if "virtuapet:policy" not in record.scopes:
            raise integration_error("virtuapet_scope_required", 403)
        await self.limiter.enforce(record.tenant_id, "policy")
        return record

    def validate_proof(self, request: PolicyRequest, record: APIKeyRecord, session: Session) -> dict[str, Any]:
        try:
            header = jwt.get_unverified_header(request.identityProof)
            if (header.get("typ") != LINK_TYPE or header.get("kid") != self.kid
                    or set(header) != {"alg", "typ", "kid"}):
                raise ValueError("wrong proof header")
            claims = jwt.decode(
                request.identityProof, self.public_key, algorithms=["ES256"], issuer=self.issuer,
                audience=self.link_audience, options={"require": list(LINK_FIELDS), "strict_aud": True},
            )
            now = int(time.time())
            if (set(claims) != LINK_FIELDS or claims["protocol"] != LINK_PROTOCOL
                    or any(not isinstance(claims.get(k), int) or isinstance(claims.get(k), bool)
                           for k in ("iat", "exp"))
                    or not 0 < claims["exp"] - claims["iat"] <= 300
                    or claims["iat"] > now or claims["exp"] <= now
                    or any(not _uuid(claims.get(k)) for k in ("sub", "tenantId", "jti", "challengeId", "nonce"))
                    or not _canonical(claims.get("providerSubject"))
                    or not _canonical(claims.get("providerOrganizationId"), 64)
                    or claims["sub"] != str(request.subject)
                    or claims["tenantId"] != str(request.tenantId)
                    or claims["providerTenantId"] != record.tenant_id
                    or self.tenant_map.get(str(request.tenantId)) != record.tenant_id):
                raise ValueError("proof context mismatch")
            tenant = session.get(Tenant, record.tenant_id)
            if (tenant is None or tenant.status != "active"
                    or tenant.clerk_organization_id != claims["providerOrganizationId"]):
                raise ValueError("provider organization no longer active")
            return claims
        except (jwt.InvalidTokenError, ValueError, TypeError, KeyError) as exc:
            raise integration_error("virtuapet_invalid_identity_proof", 403) from exc

    def decision(self, request: PolicyRequest, record: APIKeyRecord, proof: dict[str, Any]) -> str:
        entitlement: str | None = None
        required_layer8: set[str] = set()
        if (request.action == "spatial.preview.read" and request.purpose == "owner_visual_preview"
                and request.resource.startswith("pawsome3d:order:")
                and _uuid(request.resource.removeprefix("pawsome3d:order:"))):
            entitlement = "spatial.preview"
            required_layer8 = {"spatial_intelligence"}
        elif (request.action == "pawpath.nearby.read" and request.purpose == "user_requested_nearby_search"
                and request.resource == f"pawpath:user:{request.subject}"):
            entitlement = "pawpath.community"
            required_layer8 = {"api_access", "pawpath.community"}
        allowed = bool(
            entitlement and has_billing_access(record.billing_status, record.payment_grace_ends_at)
            and required_layer8.issubset(record.billing_entitlements or set())
            and set(request.requiredEntitlements).issubset({entitlement})
        )
        now = int(time.time())
        expires = min(now + 60, proof["exp"])
        if expires <= now:
            raise integration_error("virtuapet_expired_identity", 403)
        decision_id = str(uuid4())
        claims = {
            "iss": self.issuer, "aud": self.audience, "sub": str(request.subject), "iat": now,
            "exp": expires, "jti": decision_id, "protocol": POLICY_PROTOCOL,
            "tenantId": str(request.tenantId), "correlationId": str(request.correlationId),
            "requestId": str(request.requestId), "action": request.action, "resource": request.resource,
            "purpose": request.purpose, "policyVersion": POLICY_VERSION,
            "outcome": "allow" if allowed else "deny",
            "entitlements": [entitlement] if allowed else [], "obligations": [],
        }
        # No raw JWT, subject, resource, nonce, or request body in logs.
        # Process security telemetry is NOT a durable audit guarantee.
        logger.info({"event": "virtuapet_policy_decision", "decision_id": decision_id,
                     "outcome": claims["outcome"], "policy_version": POLICY_VERSION})
        return jwt.encode(claims, self.key, algorithm="ES256", headers={"kid": self.kid, "typ": POLICY_TYPE})


@lru_cache
def get_virtuapet_service() -> VirtuaPetService:
    return VirtuaPetService(get_settings())
