"""
Tests for the BO-4 spatial reasoning routes (app/api/spatial.py) added on
branch feat/bo4-spatial-routes.

These build a minimal FastAPI app containing only `spatial_router`, rather
than importing `app.main`, because `app.main` transitively imports
`app.services.api_keys`, which uses `datetime.UTC` (Python 3.11+ only) --
unrelated to spatial and pre-existing on `main`. Isolating the router keeps
this test suite runnable on Python 3.10 as well as the project's declared
3.11 minimum, and it also more precisely targets what actually changed.
"""

import os

os.environ["BACKEND_MODE"] = "memory"
os.environ["GEMINI_API_KEY"] = "test-gemini-key"

from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import get_settings

get_settings.cache_clear()

from app.api.spatial import spatial_router
from app.core.security import hash_api_secret
from app.services.auth import APIKeyRecord, InMemoryAPIKeyStore

DEV_API_KEY = "ak_live_demo.change-me-now"


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(spatial_router)
    return TestClient(app)


def test_health_reports_configured_when_gemini_key_present():
    client = build_client()
    resp = client.get("/v1/spatial/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["spatial_observe"] == "healthy"
    assert body["spatial_plan"] == "healthy"
    assert body["spatial_verify"] == "healthy"


def test_observe_rejects_missing_api_key():
    client = build_client()
    resp = client.post("/v1/spatial/observe", json={"referenceImages": []})
    assert resp.status_code == 422  # missing required X-API-Key header


def test_observe_rejects_unknown_api_key():
    client = build_client()
    resp = client.post(
        "/v1/spatial/observe",
        headers={"X-API-Key": "ak_live_demo.totally-wrong-secret"},
        json={"referenceImages": [{"versionId": 1, "url": "https://example.com/a.jpg"}]},
    )
    assert resp.status_code == 401


def test_observe_rejects_malformed_api_key():
    client = build_client()
    resp = client.post(
        "/v1/spatial/observe",
        headers={"X-API-Key": "not-a-valid-key-format"},
        json={"referenceImages": [{"versionId": 1, "url": "https://example.com/a.jpg"}]},
    )
    assert resp.status_code == 401


def test_internal_spatial_tenant_bypasses_billing_but_not_key_scope(monkeypatch):
    import app.api.spatial as spatial_api

    prefix = "ak_live_internal"
    secret = "internal-test-secret"
    record = APIKeyRecord(
        key_id="key_internal",
        tenant_id="pawsome3d",
        prefix=prefix,
        secret_hash=hash_api_secret(prefix, secret),
        scopes={"spatial:invoke"},
        allowed_models=set(),
        billing_status="inactive",
        billing_entitlements=set(),
    )
    monkeypatch.setattr(
        spatial_api,
        "_key_store",
        InMemoryAPIKeyStore({prefix: record}),
    )
    monkeypatch.setenv("INTERNAL_SPATIAL_TENANT_IDS", "pawsome3d")
    get_settings.cache_clear()

    response = build_client().post(
        "/v1/spatial/observe",
        headers={"X-API-Key": f"{prefix}.{secret}"},
        json={"referenceImages": []},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "NO_REFERENCE_IMAGES"
    get_settings.cache_clear()


def test_internal_spatial_tenant_still_requires_spatial_scope(monkeypatch):
    import app.api.spatial as spatial_api

    prefix = "ak_live_internal_no_scope"
    secret = "internal-test-secret"
    record = APIKeyRecord(
        key_id="key_internal_no_scope",
        tenant_id="pawsome3d",
        prefix=prefix,
        secret_hash=hash_api_secret(prefix, secret),
        scopes={"inference:invoke"},
        allowed_models=set(),
        billing_status="inactive",
        billing_entitlements=set(),
    )
    monkeypatch.setattr(
        spatial_api,
        "_key_store",
        InMemoryAPIKeyStore({prefix: record}),
    )
    monkeypatch.setenv("INTERNAL_SPATIAL_TENANT_IDS", "pawsome3d")
    get_settings.cache_clear()

    response = build_client().post(
        "/v1/spatial/observe",
        headers={"X-API-Key": f"{prefix}.{secret}"},
        json={"referenceImages": []},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "missing scope spatial:invoke"
    get_settings.cache_clear()


def test_observe_rejects_empty_reference_images_with_valid_key():
    client = build_client()
    resp = client.post(
        "/v1/spatial/observe",
        headers={"X-API-Key": DEV_API_KEY},
        json={"referenceImages": []},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "NO_REFERENCE_IMAGES"


def _gemini_response(content_obj: dict) -> dict:
    import json as _json

    return {
        "choices": [{"message": {"content": _json.dumps(content_obj)}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


VALID_OBSERVE_DRAFT = {
    "subjectClass": "dog_collar",
    "summary": "A red nylon collar with a metal buckle.",
    "viewCount": 1,
    "viewLabels": ["front"],
    "features": [],
    "scaleEvidence": {"hasAnchor": False, "uncertainty": 0.4},
    "occlusions": [],
}

INVALID_OBSERVE_DRAFT = {
    # missing required "summary" and "scaleEvidence" -- forces a schema-repair retry
    "subjectClass": "dog_collar",
    "viewCount": 1,
    "viewLabels": ["front"],
}


@patch("app.services.spatial_reasoning.httpx.AsyncClient.post", new_callable=AsyncMock)
def test_observe_success_with_valid_key_and_mocked_gemini(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.raise_for_status = lambda: None
    mock_post.return_value.json = lambda: _gemini_response(VALID_OBSERVE_DRAFT)

    client = build_client()
    resp = client.post(
        "/v1/spatial/observe",
        headers={"X-API-Key": DEV_API_KEY},
        json={"referenceImages": [{"versionId": 1, "url": "https://example.com/a.jpg"}]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["subjectClass"] == "dog_collar"
    # server-computed hash, never trust the model to hash its own output
    assert len(body["observationHash"]) == 64
    assert mock_post.call_count == 1


@patch("app.services.spatial_reasoning.httpx.AsyncClient.post", new_callable=AsyncMock)
def test_observe_schema_repair_retry_recovers_from_bad_first_response(mock_post):
    responses = [
        _gemini_response(INVALID_OBSERVE_DRAFT),
        _gemini_response(VALID_OBSERVE_DRAFT),
    ]

    def _side_effect(*args, **kwargs):
        r = AsyncMock()
        r.status_code = 200
        r.raise_for_status = lambda: None
        r.json = lambda: responses.pop(0)
        return r

    mock_post.side_effect = _side_effect

    client = build_client()
    resp = client.post(
        "/v1/spatial/observe",
        headers={"X-API-Key": DEV_API_KEY},
        json={"referenceImages": [{"versionId": 1, "url": "https://example.com/a.jpg"}]},
    )
    assert resp.status_code == 200, resp.text
    assert mock_post.call_count == 2  # one bad attempt + one repair retry


@patch("app.services.spatial_reasoning.httpx.AsyncClient.post", new_callable=AsyncMock)
def test_observe_fails_closed_after_exhausting_repair_attempts(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.raise_for_status = lambda: None
    mock_post.return_value.json = lambda: _gemini_response(INVALID_OBSERVE_DRAFT)

    client = build_client()
    resp = client.post(
        "/v1/spatial/observe",
        headers={"X-API-Key": DEV_API_KEY},
        json={"referenceImages": [{"versionId": 1, "url": "https://example.com/a.jpg"}]},
    )
    assert resp.status_code == 502
    assert resp.json()["detail"]["code"] == "INVALID_MODEL_OUTPUT"
    assert mock_post.call_count == 2  # initial attempt + MAX_SCHEMA_REPAIR_ATTEMPTS(1)


def test_verify_rejects_empty_draft_images_with_valid_key():
    client = build_client()
    resp = client.post(
        "/v1/spatial/verify",
        headers={"X-API-Key": DEV_API_KEY},
        json={
            "observation": {
                "subjectClass": "dog_collar",
                "summary": "s",
                "viewCount": 1,
                "viewLabels": ["front"],
                "features": [],
                "scaleEvidence": {"hasAnchor": False, "uncertainty": 0.4},
                "occlusions": [],
                "observationHash": "a" * 64,
            },
            "draftImages": [],
            "attemptHash": "b" * 64,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "NO_DRAFT_IMAGES"


def test_gemini_provider_has_no_dangling_mamavnav_reference():
    from app.providers import gemini as gemini_provider

    assert not hasattr(gemini_provider, "MAMAVNAV_SYSTEM_PROMPT")
    assert "helpful" in gemini_provider.DEFAULT_SYSTEM_PROMPT.lower()
