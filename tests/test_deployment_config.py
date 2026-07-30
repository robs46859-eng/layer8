from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_render_postgres_url_uses_installed_psycopg_driver():
    settings = Settings(DATABASE_URL="postgresql://salti8:secret@database.internal:5432/salti8")

    assert settings.database_url == (
        "postgresql+psycopg://salti8:secret@database.internal:5432/salti8"
    )


def test_blank_cloud_endpoints_use_provider_defaults():
    settings = Settings(AWS_ENDPOINT_URL="", S3_ENDPOINT_URL="  ")

    assert settings.aws_endpoint_url is None
    assert settings.s3_endpoint_url is None


def test_cors_preflight_allows_salti8_and_rejects_untrusted_origin(monkeypatch):
    monkeypatch.setenv("BACKEND_MODE", "memory")
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "https://salti8.com,https://www.salti8.com",
    )
    get_settings.cache_clear()
    client = TestClient(create_app())

    trusted = client.options(
        "/v1/customer/billing",
        headers={
            "Origin": "https://salti8.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert trusted.status_code == 200
    assert trusted.headers["access-control-allow-origin"] == "https://salti8.com"

    untrusted = client.options(
        "/v1/customer/billing",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in untrusted.headers
    get_settings.cache_clear()


def test_production_cors_removes_localhost_origins():
    settings = Settings(
        ENVIRONMENT="production",
        CORS_ALLOWED_ORIGINS=(
            "http://localhost:3000,http://127.0.0.1:3000,"
            "https://salti8.com,https://www.salti8.com"
        ),
    )

    assert settings.cors_origin_list == [
        "https://salti8.com",
        "https://www.salti8.com",
    ]


def test_internal_spatial_tenants_are_explicit_and_trimmed():
    settings = Settings(INTERNAL_SPATIAL_TENANT_IDS=" pawsome3d,internal-cad ,,")
    assert settings.internal_spatial_tenant_id_set == {"pawsome3d", "internal-cad"}


def test_internal_spatial_tenants_default_closed():
    settings = Settings()
    assert settings.internal_spatial_tenant_id_set == set()


def test_development_cors_keeps_local_origins():
    settings = Settings(ENVIRONMENT="development")

    assert "http://localhost:3000" in settings.cors_origin_list
    assert "http://127.0.0.1:3000" in settings.cors_origin_list


def test_cors_wildcard_is_rejected():
    try:
        Settings(CORS_ALLOWED_ORIGINS="*")
    except ValidationError as exc:
        assert "must list explicit trusted origins" in str(exc)
    else:
        raise AssertionError("expected wildcard CORS configuration to fail")


def test_render_blueprint_uses_paid_recoverable_production_resources():
    blueprint = (REPOSITORY_ROOT / "render.yaml").read_text()

    assert "plan: free" not in blueprint
    assert "plan: starter" in blueprint
    assert "plan: basic-1gb" in blueprint
    assert "storageAutoscalingEnabled: true" in blueprint


def test_render_blueprint_gates_deploy_on_readiness_and_runs_migrations_once():
    blueprint = (REPOSITORY_ROOT / "render.yaml").read_text()

    assert "autoDeployTrigger: checksPass" in blueprint
    assert "preDeployCommand: alembic upgrade head" in blueprint
    assert 'startCommand: exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"' in blueprint
    assert "healthCheckPath: /readyz" in blueprint
    assert "startCommand: alembic upgrade head" not in blueprint
