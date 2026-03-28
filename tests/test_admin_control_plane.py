import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_engine, get_session_factory
from app.main import create_app
from app.services.auth import AuthService, PostgresAPIKeyStore
from app.services.context import RequestContext
from app.schemas.inference import InferenceRequest, Message


def _reset_settings() -> None:
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


def _build_client(db_path: Path) -> TestClient:
    os.environ["BACKEND_MODE"] = "memory"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["ADMIN_API_TOKEN"] = "test-admin-token"
    _reset_settings()
    engine = create_engine(f"sqlite:///{db_path}", future=True, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    app = create_app()
    return TestClient(app)


def _admin_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-admin-token"}


def test_tenant_crud_and_disable_blocks_runtime_auth(tmp_path):
    client = _build_client(tmp_path / "admin.sqlite3")

    create_response = client.post(
        "/admin/tenants",
        headers=_admin_headers(),
        json={"tenant_id": "tenant_alpha", "name": "Tenant Alpha", "data_residency": "us"},
    )
    assert create_response.status_code == 201
    assert create_response.json()["status"] == "active"

    list_response = client.get("/admin/tenants", headers=_admin_headers())
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == ["tenant_alpha"]

    update_response = client.patch(
        "/admin/tenants/tenant_alpha",
        headers=_admin_headers(),
        json={"name": "Tenant Alpha Prime", "data_residency": "eu"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Tenant Alpha Prime"
    assert update_response.json()["data_residency"] == "eu"

    key_response = client.post(
        "/admin/tenants/tenant_alpha/api-keys",
        headers=_admin_headers(),
        json={"scopes": ["inference:invoke"], "allowed_models": ["gpt-4.1-mini"]},
    )
    assert key_response.status_code == 201
    raw_key = key_response.json()["api_key"]

    disable_response = client.post("/admin/tenants/tenant_alpha/disable", headers=_admin_headers())
    assert disable_response.status_code == 200
    assert disable_response.json()["status"] == "disabled"
    assert disable_response.json()["disabled_at"] is not None

    auth_service = AuthService(PostgresAPIKeyStore())
    context = RequestContext.from_request(
        payload=InferenceRequest(model="gpt-4.1-mini", messages=[Message(role="user", content="hi")]),
        presented_api_key=raw_key,
        idempotency_key=None,
        client_host="127.0.0.1",
    )
    import asyncio

    try:
        asyncio.run(auth_service.authenticate(context))
    except PermissionError as exc:
        assert "tenant is inactive" in str(exc)
    else:
        raise AssertionError("expected disabled tenant auth failure")


def test_api_key_revoke_and_rotate_runtime_behavior(tmp_path):
    client = _build_client(tmp_path / "keys.sqlite3")

    tenant_response = client.post(
        "/admin/tenants",
        headers=_admin_headers(),
        json={"tenant_id": "tenant_bravo", "name": "Tenant Bravo"},
    )
    assert tenant_response.status_code == 201

    create_key = client.post(
        "/admin/tenants/tenant_bravo/api-keys",
        headers=_admin_headers(),
        json={"scopes": ["inference:invoke"], "allowed_models": ["gpt-4.1-mini"]},
    )
    assert create_key.status_code == 201
    original = create_key.json()
    original_raw_key = original["api_key"]
    original_key_id = original["id"]

    revoke_response = client.post(f"/admin/api-keys/{original_key_id}/revoke", headers=_admin_headers())
    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "revoked"
    assert revoke_response.json()["revoked_at"] is not None

    auth_service = AuthService(PostgresAPIKeyStore())
    revoked_context = RequestContext.from_request(
        payload=InferenceRequest(model="gpt-4.1-mini", messages=[Message(role="user", content="hi")]),
        presented_api_key=original_raw_key,
        idempotency_key=None,
        client_host="127.0.0.1",
    )
    import asyncio

    try:
        asyncio.run(auth_service.authenticate(revoked_context))
    except PermissionError as exc:
        assert "api key is inactive" in str(exc)
    else:
        raise AssertionError("expected revoked key auth failure")

    second_key = client.post(
        "/admin/tenants/tenant_bravo/api-keys",
        headers=_admin_headers(),
        json={"scopes": ["inference:invoke"], "allowed_models": ["gpt-4.1-mini"]},
    )
    assert second_key.status_code == 201
    second_key_id = second_key.json()["id"]

    rotate_response = client.post(
        f"/admin/api-keys/{second_key_id}/rotate",
        headers=_admin_headers(),
    )
    assert rotate_response.status_code == 200
    rotated = rotate_response.json()
    assert rotated["id"] != second_key_id
    assert rotated["api_key"].startswith("ak_live_")

    old_key_list = client.get("/admin/tenants/tenant_bravo/api-keys", headers=_admin_headers())
    assert old_key_list.status_code == 200
    old_key_status = {item["id"]: item["status"] for item in old_key_list.json()}
    assert old_key_status[second_key_id] == "revoked"
    assert old_key_status[rotated["id"]] == "active"

    active_context = RequestContext.from_request(
        payload=InferenceRequest(model="gpt-4.1-mini", messages=[Message(role="user", content="hi")]),
        presented_api_key=rotated["api_key"],
        idempotency_key=None,
        client_host="127.0.0.1",
    )
    authenticated = asyncio.run(auth_service.authenticate(active_context))
    assert authenticated.tenant_id == "tenant_bravo"


def test_admin_routes_require_bearer_token(tmp_path):
    client = _build_client(tmp_path / "auth.sqlite3")

    missing = client.get("/admin/tenants")
    assert missing.status_code == 401

    invalid = client.get("/admin/tenants", headers={"Authorization": "Bearer wrong-token"})
    assert invalid.status_code == 403
