"""Real route, JWT crypto and stored-key tests; no cloud credentials or paid requests."""

import json
import time
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
import redis
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.api import billing, dependencies
from app.api.billing import customer_billing_router
from app.api.dependencies import get_db_session
from app.api.virtuapet import virtuapet_router
from app.core.config import Settings
from app.core.security import hash_api_secret
from app.db.base import Base
from app.db.models import APIKey, BillingAccount, Tenant
from app.services.auth import PostgresAPIKeyStore
from app.services.virtuapet import (
    LINK_FIELDS,
    LINK_TYPE,
    POLICY_TYPE,
    IntegrationLimiter,
    VirtuaPetService,
    get_virtuapet_service,
)

VP_SUBJECT = "11111111-1111-4111-8111-111111111111"
VP_TENANT = "22222222-2222-4222-8222-222222222222"
ORDER = "33333333-3333-4333-8333-333333333333"
PREFIX = "ak_test_vp_policy"
SECRET = "fixture-secret-never-a-real-key"
API_KEY = f"{PREFIX}.{SECRET}"
BASE = "/v1/integrations/virtuapet"


def build_runtime(db_path):
    """Reusable test bridge: ephemeral keys and SQLite; same router and stored-key auth."""
    signing_key = ec.generate_private_key(ec.SECP256R1())
    clerk_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    settings = Settings(
        _env_file=None, ENVIRONMENT="test", BACKEND_MODE="memory",
        VIRTUAPET_INTEGRATION_ENABLED=True,
        VIRTUAPET_SIGNING_PRIVATE_KEY=signing_key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode(),
        VIRTUAPET_SIGNING_KEY_ID="fixture-p256-1",
        VIRTUAPET_POLICY_ISSUER="https://layer8.example.com",
        VIRTUAPET_POLICY_AUDIENCE="virtuapet-policy",
        VIRTUAPET_LINK_AUDIENCE="virtuapet-links",
        VIRTUAPET_TENANT_MAP_JSON=json.dumps({VP_TENANT: "tenant_vp"}),
        CLERK_JWT_KEY=clerk_key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode(),
        CLERK_ISSUER="https://clerk.example.com", CLERK_AUTHORIZED_PARTIES="https://salti8.com",
        SELF_SERVICE_SIGNUP_ENABLED=True,
        INTERNAL_SPATIAL_TENANT_IDS="tenant_vp", ADMIN_API_TOKEN="fixture-admin",
    )
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        session.add(Tenant(id="tenant_vp", name="VirtuaPet test", status="active",
                           clerk_organization_id="org_vp"))
        session.add(APIKey(id="vp_policy_key", tenant_id="tenant_vp", prefix=PREFIX,
                           secret_hash=hash_api_secret(PREFIX, SECRET), status="active",
                           scopes=["virtuapet:policy"], allowed_models=[]))
        session.add(BillingAccount(id="vp_billing", tenant_id="tenant_vp",
                                   subscription_status="active", plan_key="team",
                                   entitlements=["api_access", "spatial_intelligence"]))
        session.commit()
    key_store = PostgresAPIKeyStore()
    key_store.session_factory = factory
    service = VirtuaPetService(settings, key_store=key_store)
    app = FastAPI()
    app.include_router(virtuapet_router)
    app.dependency_overrides[get_virtuapet_service] = lambda: service

    def database():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = database
    return SimpleNamespace(app=app, client=TestClient(app), service=service, settings=settings,
                           engine=engine, factory=factory, signing_key=signing_key,
                           clerk_key=clerk_key)


@pytest.fixture
def runtime(tmp_path):
    value = build_runtime(tmp_path / "vp.sqlite")
    yield value
    value.client.close()
    value.engine.dispose()


def clerk_token(runtime, *, version=1, **overrides):
    now = int(time.time())
    claims = {"iss": runtime.settings.clerk_issuer, "sub": "user_real_clerk",
              "azp": "https://salti8.com", "iat": now, "nbf": now, "exp": now + 3600}
    claims.update({"v": 2, "o": {"id": "org_vp"}} if version == 2 else {"org_id": "org_vp"})
    claims.update(overrides)
    return jwt.encode(claims, runtime.clerk_key, algorithm="RS256")


@pytest.fixture
def customer_runtime(runtime, monkeypatch):
    monkeypatch.setattr(dependencies, "get_settings", lambda: runtime.settings)
    monkeypatch.setattr(billing, "get_settings", lambda: runtime.settings)
    runtime.app.include_router(customer_billing_router)
    return runtime


@pytest.mark.parametrize("version", [1, 2])
def test_clerk_organization_formats_keep_customer_and_link_tenants_separate(customer_runtime, version):
    runtime = customer_runtime
    other_vp_tenant = str(uuid4())
    runtime.service.tenant_map[other_vp_tenant] = "tenant_other"
    with runtime.factory() as session:
        session.add(Tenant(id="tenant_other", name="Other tenant", status="active",
                           clerk_organization_id="org_other"))
        session.commit()

    for org_id, tenant_id, vp_tenant in [
        ("org_vp", "tenant_vp", VP_TENANT),
        ("org_other", "tenant_other", other_vp_tenant),
    ]:
        org_claim = {"o": {"id": org_id}} if version == 2 else {"org_id": org_id}
        token = clerk_token(runtime, version=version, sub=f"user_{tenant_id}", **org_claim)
        headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": "untrusted_tenant"}
        response = runtime.client.get("/v1/customer/billing?tenant_id=untrusted_tenant",
                                      headers=headers)
        assert response.status_code == 200
        assert response.json()["tenant_id"] == tenant_id
        response = runtime.client.post(BASE + "/link-proof", headers=headers,
            json={**link_body(), "tenantId": vp_tenant})
        assert response.status_code == 200
        claims = jwt.decode(response.json()["proofToken"], runtime.signing_key.public_key(),
                            algorithms=["ES256"], issuer=runtime.service.issuer,
                            audience="virtuapet-links")
        assert claims["providerTenantId"] == tenant_id
        assert claims["providerOrganizationId"] == org_id
        wrong_tenant = other_vp_tenant if vp_tenant == VP_TENANT else VP_TENANT
        assert runtime.client.post(BASE + "/link-proof", headers=headers,
            json={**link_body(), "tenantId": wrong_tenant}).status_code == 403


@pytest.mark.parametrize("override", [
    {"o": None}, {"o": []}, {"o": {}}, {"o": {"id": ["org_vp"]}},
    {"o": {"id": " org_vp"}}, {"o": {"id": "org_vp"}, "org_id": "org_other"},
    {"o": {}, "org_id": "org_vp"}, {"org_id": None},
])
def test_bad_v2_claims_cannot_select_or_provision_a_tenant(customer_runtime, override):
    runtime = customer_runtime
    headers = {"Authorization": f"Bearer {clerk_token(runtime, version=2, **override)}"}
    with runtime.factory() as session:
        before = session.scalar(select(func.count()).select_from(Tenant))
    assert runtime.client.get("/v1/customer/billing", headers=headers).status_code == 403
    assert runtime.client.post(BASE + "/link-proof", json=link_body(),
                               headers=headers).status_code == 403
    with runtime.factory() as session:
        assert session.scalar(select(func.count()).select_from(Tenant)) == before


def test_v2_organization_is_used_only_after_signature_verification(customer_runtime):
    runtime = customer_runtime
    claims = jwt.decode(clerk_token(runtime, version=2), options={"verify_signature": False})
    forged = jwt.encode(claims, rsa.generate_private_key(public_exponent=65537, key_size=2048),
                        algorithm="RS256")
    headers = {"Authorization": f"Bearer {forged}"}
    assert runtime.client.get("/v1/customer/billing", headers=headers).status_code == 401
    assert runtime.client.post(BASE + "/link-proof", json=link_body(),
                               headers=headers).status_code == 401


def link_body():
    return {"subject": VP_SUBJECT, "tenantId": VP_TENANT,
            "challengeId": str(uuid4()), "nonce": str(uuid4())}


def proof(runtime, **overrides):
    response = runtime.client.post(BASE + "/link-proof", json={**link_body(), **overrides},
                                   headers={"Authorization": f"Bearer {clerk_token(runtime)}"})
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    return response.json()["proofToken"]


def policy_body(runtime, token=None, **overrides):
    return {"protocol": "virtuapet.layer8.policy.v1", "subject": VP_SUBJECT,
            "tenantId": VP_TENANT, "requestId": str(uuid4()), "correlationId": str(uuid4()),
            "action": "spatial.preview.read", "resource": f"pawsome3d:order:{ORDER}",
            "purpose": "owner_visual_preview", "requiredEntitlements": ["spatial.preview"],
            "identityProof": token or proof(runtime), **overrides}


def post_policy(runtime, body, token=API_KEY):
    return runtime.client.post(BASE + "/policy", json=body,
                               headers={"Authorization": f"Bearer {token}"})


def decision(runtime, response):
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    token = response.json()["decisionToken"]
    assert jwt.get_unverified_header(token) == {
        "alg": "ES256", "kid": "fixture-p256-1", "typ": POLICY_TYPE,
    }
    return jwt.decode(token, runtime.signing_key.public_key(), algorithms=["ES256"],
                      issuer=runtime.settings.virtuapet_policy_issuer, audience="virtuapet-policy")


def change(runtime, model, key, **values):
    with runtime.factory() as session:
        row = session.get(model, key)
        for field, value in values.items():
            setattr(row, field, value)
        session.commit()


def test_default_off_and_missing_config_fail_closed():
    with pytest.raises(HTTPException, match="virtuapet_disabled"):
        VirtuaPetService(Settings(_env_file=None, VIRTUAPET_INTEGRATION_ENABLED=False))
    with pytest.raises(HTTPException, match="virtuapet_unconfigured"):
        VirtuaPetService(Settings(_env_file=None, VIRTUAPET_INTEGRATION_ENABLED=True,
                                 ENVIRONMENT="test", VIRTUAPET_SIGNING_KEY_ID=""))


@pytest.mark.parametrize("environment", ["production", "prod", "staging", "unknown"])
def test_memory_is_not_a_production_backend(runtime, environment):
    with pytest.raises(HTTPException, match="persistent_backend_required"):
        VirtuaPetService(runtime.settings.model_copy(update={"environment": environment}))


def test_proof_uses_verified_clerk_identity_and_exact_claims(runtime):
    token = proof(runtime)
    assert jwt.get_unverified_header(token)["typ"] == LINK_TYPE
    claims = jwt.decode(token, runtime.signing_key.public_key(), algorithms=["ES256"],
                        issuer=runtime.service.issuer, audience="virtuapet-links")
    assert set(claims) == LINK_FIELDS
    assert claims["providerSubject"] == "user_real_clerk"
    assert claims["providerTenantId"] == "tenant_vp"
    assert claims["providerOrganizationId"] == "org_vp"
    assert claims["sub"] == VP_SUBJECT
    assert 0 < claims["exp"] - claims["iat"] <= 300


@pytest.mark.parametrize("override", [
    {"exp": 1}, {"nbf": 4_000_000_000}, {"iat": 4_000_000_000},
    {"iss": "https://attacker.example.com"}, {"azp": "https://attacker.example.com"},
    {"org_id": None}, {"org_id": "org_unknown"}, {"sub": ""}, {"azp": ["https://salti8.com"]},
])
def test_invalid_clerk_claims_rejected(runtime, override):
    response = runtime.client.post(BASE + "/link-proof", json=link_body(),
        headers={"Authorization": f"Bearer {clerk_token(runtime, **override)}"})
    assert response.status_code in {401, 403}


def test_wrong_signer_admin_and_identity_headers_are_not_auth(runtime):
    for token in ["fixture-admin", API_KEY, "unsigned-session"]:
        response = runtime.client.post(BASE + "/link-proof", json=link_body(), headers={
            "Authorization": f"Bearer {token}", "X-User-Id": "user_real_clerk", "X-Tenant-Id": "tenant_vp",
        })
        assert response.status_code == 401
    payload = jwt.decode(clerk_token(runtime), options={"verify_signature": False})
    forged = jwt.encode(payload, rsa.generate_private_key(public_exponent=65537, key_size=2048),
                        algorithm="RS256")
    assert runtime.client.post(BASE + "/link-proof", json=link_body(),
        headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_unknown_org_does_not_provision_even_if_signup_enabled(runtime):
    with runtime.factory() as session:
        before = session.scalar(select(func.count()).select_from(Tenant))
    runtime.client.post(BASE + "/link-proof", json=link_body(),
        headers={"Authorization": f"Bearer {clerk_token(runtime, org_id='org_unknown')}"})
    with runtime.factory() as session:
        assert session.scalar(select(func.count()).select_from(Tenant)) == before


def test_tenant_mapping_and_active_tenant_required_for_link(runtime):
    response = runtime.client.post(BASE + "/link-proof", json={**link_body(), "tenantId": str(uuid4())},
        headers={"Authorization": f"Bearer {clerk_token(runtime)}"})
    assert response.status_code == 403
    change(runtime, Tenant, "tenant_vp", status="disabled")
    assert runtime.client.post(BASE + "/link-proof", json=link_body(),
        headers={"Authorization": f"Bearer {clerk_token(runtime)}"}).status_code == 403


def test_policy_signature_echoes_request_and_grants_only_expected_entitlement(runtime):
    body = policy_body(runtime)
    claims = decision(runtime, post_policy(runtime, body))
    for name in ("tenantId", "correlationId", "requestId", "action", "resource", "purpose", "protocol"):
        assert claims[name] == body[name]
    assert claims["sub"] == VP_SUBJECT
    assert claims["outcome"] == "allow"
    assert claims["entitlements"] == ["spatial.preview"]
    assert claims["obligations"] == []
    assert 0 < claims["exp"] - claims["iat"] <= 60
    assert set(claims) == {"iss", "aud", "sub", "iat", "exp", "jti", "protocol", "tenantId",
        "correlationId", "requestId", "action", "resource", "purpose", "policyVersion", "outcome",
        "entitlements", "obligations"}


@pytest.mark.parametrize("token", ["fixture-admin", "ak_live_demo.change-me-now", "bad-format",
                                  f"{PREFIX}.wrong-secret", "", "unknown.secret"])
def test_policy_requires_real_scoped_hashed_key(runtime, token):
    assert post_policy(runtime, policy_body(runtime), token=token).status_code == 401


@pytest.mark.parametrize("values,status", [
    ({"scopes": ["spatial:invoke", "inference:invoke"]}, 403), ({"status": "revoked"}, 401),
])
def test_key_scope_and_revocation_are_fresh(runtime, values, status):
    body = policy_body(runtime)
    assert post_policy(runtime, body).status_code == 200
    change(runtime, APIKey, "vp_policy_key", **values)
    assert post_policy(runtime, {**body, "requestId": str(uuid4())}).status_code == status


@pytest.mark.parametrize("values", [
    {"subscription_status": "canceled"}, {"subscription_status": "inactive"},
    {"entitlements": ["api_access"]}, {"subscription_status": "past_due", "payment_grace_ends_at": None},
    {"subscription_status": "past_due", "payment_grace_ends_at": datetime.now(UTC) - timedelta(days=1)},
])
def test_billing_is_fresh_and_internal_spatial_does_not_bypass_it(runtime, values):
    token = proof(runtime)
    assert decision(runtime, post_policy(runtime, policy_body(runtime, token)))['outcome'] == "allow"
    change(runtime, BillingAccount, "vp_billing", **values)
    result = decision(runtime, post_policy(runtime, policy_body(runtime, token)))
    assert result["outcome"] == "deny"
    assert result["entitlements"] == []


def test_pawpath_requires_explicit_community_entitlement(runtime):
    body = policy_body(runtime, action="pawpath.nearby.read", resource=f"pawpath:user:{VP_SUBJECT}",
                       purpose="user_requested_nearby_search", requiredEntitlements=["pawpath.community"])
    assert decision(runtime, post_policy(runtime, body))["outcome"] == "deny"
    change(runtime, BillingAccount, "vp_billing", entitlements=["api_access", "pawpath.community"])
    result = decision(runtime, post_policy(runtime, {**body, "requestId": str(uuid4())}))
    assert result["outcome"] == "allow" and result["entitlements"] == ["pawpath.community"]
    change(runtime, BillingAccount, "vp_billing", entitlements=["pawpath.community"])
    assert decision(runtime, post_policy(runtime, {**body, "requestId": str(uuid4())}))["outcome"] == "deny"


@pytest.mark.parametrize("override", [
    {"action": "clinical.surgery"}, {"resource": "pawsome3d:order:all"},
    {"purpose": "diagnosis"}, {"requiredEntitlements": ["platform.admin"]},
    {"action": "pawpath.nearby.read", "resource": f"pawpath:user:{ORDER}",
     "purpose": "user_requested_nearby_search", "requiredEntitlements": ["pawpath.community"]},
])
def test_action_resource_purpose_allowlist_cannot_be_relaxed_by_caller(runtime, override):
    assert decision(runtime, post_policy(runtime, policy_body(runtime, **override)))["outcome"] == "deny"


@pytest.mark.parametrize("override", [
    {"subject": ORDER}, {"tenantId": ORDER},
])
def test_proof_cannot_be_replayed_for_another_caller_or_tenant(runtime, override):
    assert post_policy(runtime, policy_body(runtime, **override)).status_code == 403


@pytest.mark.parametrize("claim,value", [
    ("exp", 1), ("iat", 4_000_000_000), ("aud", "virtuapet-policy"),
    ("providerSubject", ""), ("providerTenantId", "tenant_other"),
    ("providerOrganizationId", "org_other"), ("protocol", "other"), ("jti", "not-uuid"),
])
def test_invalid_signed_proofs_rejected(runtime, claim, value):
    claims = jwt.decode(proof(runtime), options={"verify_signature": False})
    claims[claim] = value
    token = jwt.encode(claims, runtime.signing_key, algorithm="ES256",
                       headers={"typ": LINK_TYPE, "kid": runtime.service.kid})
    assert post_policy(runtime, policy_body(runtime, token)).status_code == 403


def test_token_headers_unknown_claims_and_excessive_proof_lifetime_rejected(runtime):
    claims = jwt.decode(proof(runtime), options={"verify_signature": False})
    variants = [
        (claims, {"typ": POLICY_TYPE, "kid": runtime.service.kid}),
        (claims, {"typ": LINK_TYPE, "kid": "wrong"}),
        ({**claims, "extra": "no"}, {"typ": LINK_TYPE, "kid": runtime.service.kid}),
        ({**claims, "exp": claims["iat"] + 301}, {"typ": LINK_TYPE, "kid": runtime.service.kid}),
    ]
    for payload, headers in variants:
        token = jwt.encode(payload, runtime.signing_key, algorithm="ES256", headers=headers)
        assert post_policy(runtime, policy_body(runtime, token)).status_code == 403


def test_tenant_binding_change_and_disable_invalidate_existing_proof(runtime):
    token = proof(runtime)
    change(runtime, Tenant, "tenant_vp", clerk_organization_id="org_reassigned")
    assert post_policy(runtime, policy_body(runtime, token)).status_code == 403
    change(runtime, Tenant, "tenant_vp", status="disabled", clerk_organization_id="org_vp")
    assert post_policy(runtime, policy_body(runtime, token)).status_code == 401


def test_duplicate_policy_request_id_is_rejected(runtime):
    body = policy_body(runtime)
    assert post_policy(runtime, body).status_code == 200
    assert post_policy(runtime, body).status_code == 409
    assert post_policy(runtime, {**body, "requestId": str(uuid4())}).status_code == 200


def test_policy_expiry_cannot_outlive_proof(runtime):
    claims = jwt.decode(proof(runtime), options={"verify_signature": False})
    claims["exp"] = int(time.time()) + 10
    token = jwt.encode(claims, runtime.signing_key, algorithm="ES256",
                       headers={"typ": LINK_TYPE, "kid": runtime.service.kid})
    assert decision(runtime, post_policy(runtime, policy_body(runtime, token)))["exp"] == claims["exp"]


def test_strict_contract_and_validation_errors_never_echo_proofs(runtime):
    token = proof(runtime)
    for extra in [{"providerSubject": "forged"}, {"action": " x "},
                  {"requiredEntitlements": ["spatial.preview", "spatial.preview"]}]:
        response = post_policy(runtime, policy_body(runtime, token, **extra))
        assert response.status_code == 422
        assert token not in response.text
        assert response.headers["cache-control"] == "no-store"
    response = runtime.client.post(BASE + "/policy", content=b"x" * 32769)
    assert response.status_code == 413


def test_request_rate_limit_enforced(runtime):
    runtime.service.limiter.memory.limit_per_minute = 1
    body = policy_body(runtime)
    assert post_policy(runtime, body).status_code == 200
    assert post_policy(runtime, {**body, "requestId": str(uuid4())}).status_code == 429


@pytest.mark.asyncio
async def test_redis_atomic_limits_and_replay_fail_closed(runtime):
    limiter = IntegrationLimiter(runtime.settings.model_copy(update={"backend_mode": "self_hosted"}))
    assert limiter.memory is None

    class RedisStub:
        def __init__(self):
            self.calls = []
        def eval(self, *args):
            self.calls.append(args)
            return 1
        def set(self, *args, **kwargs):
            assert kwargs == {"ex": 300, "nx": True}

    limiter.client = RedisStub()
    await limiter.enforce("tenant_vp", "policy")
    assert "INCR" in limiter.client.calls[0][0] and "EXPIRE" in limiter.client.calls[0][0]
    with pytest.raises(HTTPException, match="request_replayed"):
        await limiter.reserve_request("tenant_vp", str(uuid4()))

    class UnavailableRedis:
        def eval(self, *args):
            raise redis.ConnectionError("secret-host-will-not-be-returned")
        def set(self, *args, **kwargs):
            raise redis.ConnectionError("secret-host-will-not-be-returned")

    limiter.client = UnavailableRedis()
    with pytest.raises(HTTPException, match="rate_limit_unavailable"):
        await limiter.enforce("tenant_vp", "policy")
    with pytest.raises(HTTPException, match="replay_store_unavailable"):
        await limiter.reserve_request("tenant_vp", str(uuid4()))


def test_no_tokens_or_personal_identity_in_security_logs(runtime, caplog):
    body = policy_body(runtime)
    with caplog.at_level("INFO"):
        response = post_policy(runtime, body)
    assert response.status_code == 200
    for secret in [API_KEY, body["identityProof"], "user_real_clerk", VP_SUBJECT, ORDER]:
        assert secret not in caplog.text


def test_unexpected_backend_failure_is_redacted_and_not_cached(runtime, monkeypatch):
    body = policy_body(runtime)

    def unavailable(*args):
        raise RuntimeError("backend password and sensitive request data")

    monkeypatch.setattr(runtime.service, "validate_proof", unavailable)
    response = post_policy(runtime, body)
    assert response.status_code == 503
    assert response.json() == {"detail": "virtuapet_unavailable"}
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("setting,value", [
    ("virtuapet_signing_private_key", "not-a-private-key"),
    ("virtuapet_signing_key_id", ""),
    ("virtuapet_link_audience", "virtuapet-policy"),
    ("virtuapet_tenant_map_json", "{}"),
    ("virtuapet_tenant_map_json", '{"not-a-uuid":"tenant_vp"}'),
    ("virtuapet_tenant_map_json", "null"),
])
def test_bad_key_trust_or_mapping_is_never_usable(runtime, setting, value):
    with pytest.raises(HTTPException, match="virtuapet_unconfigured"):
        VirtuaPetService(runtime.settings.model_copy(update={setting: value}))


def test_wrong_signature_hmac_and_malformed_proof_fail_closed(runtime):
    claims = jwt.decode(proof(runtime), options={"verify_signature": False})
    for token in [
        "not-a-token",
        jwt.encode(claims, ec.generate_private_key(ec.SECP256R1()), algorithm="ES256",
                   headers={"kid": runtime.service.kid, "typ": LINK_TYPE}),
        jwt.encode(claims, "fixture-hmac-wrong-algorithm-secret", algorithm="HS256",
                   headers={"kid": runtime.service.kid, "typ": LINK_TYPE}),
    ]:
        assert post_policy(runtime, policy_body(runtime, token)).status_code == 403


def test_link_proof_cannot_outlive_clerk_session(runtime):
    expiry = int(time.time()) + 20
    response = runtime.client.post(BASE + "/link-proof", json=link_body(),
        headers={"Authorization": f"Bearer {clerk_token(runtime, exp=expiry)}"})
    assert response.status_code == 200
    claims = jwt.decode(response.json()["proofToken"], options={"verify_signature": False})
    assert claims["exp"] == expiry


def test_missing_authorized_parties_and_missing_expiration_fail_closed(runtime):
    runtime.settings.clerk_authorized_parties = ""
    response = runtime.client.post(BASE + "/link-proof", json=link_body(),
        headers={"Authorization": f"Bearer {clerk_token(runtime)}"})
    assert response.status_code == 503
    runtime.settings.clerk_authorized_parties = "https://salti8.com"
    claims = jwt.decode(clerk_token(runtime), options={"verify_signature": False})
    del claims["exp"]
    token = jwt.encode(claims, runtime.clerk_key, algorithm="RS256")
    assert runtime.client.post(BASE + "/link-proof", json=link_body(),
        headers={"Authorization": f"Bearer {token}"}).status_code == 401
