import hashlib
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base
from app.db.models import BillingAccount, StripeWebhookEvent, Tenant
from app.db.session import get_engine, get_session_factory
from app.main import create_app
from app.services.billing import StripeBillingService


def _reset_settings() -> None:
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


def _build_client(db_path: Path) -> TestClient:
    os.environ["BACKEND_MODE"] = "memory"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["ADMIN_API_TOKEN"] = "test-admin-token"
    os.environ["STRIPE_SECRET_KEY"] = ""
    os.environ["STRIPE_WEBHOOK_SECRET"] = ""
    os.environ["STRIPE_LIVE_MODE"] = "false"
    os.environ["CLERK_JWT_KEY"] = ""
    os.environ["CLERK_ISSUER"] = ""
    _reset_settings()
    engine = create_engine(
        f"sqlite:///{db_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    return TestClient(create_app())


def _admin_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-admin-token"}


def test_billing_routes_require_admin_and_configuration(tmp_path):
    client = _build_client(tmp_path / "billing-routes.sqlite3")

    missing_auth = client.post(
        "/v1/billing/checkout",
        json={"tenant_id": "tenant_alpha", "plan_key": "team"},
    )
    assert missing_auth.status_code == 401

    tenant = client.post(
        "/admin/tenants",
        headers=_admin_headers(),
        json={"tenant_id": "tenant_alpha", "name": "Tenant Alpha"},
    )
    assert tenant.status_code == 201

    unconfigured = client.post(
        "/v1/billing/checkout",
        headers={**_admin_headers(), "Idempotency-Key": "attempt-1"},
        json={"tenant_id": "tenant_alpha", "plan_key": "team"},
    )
    assert unconfigured.status_code == 503
    assert unconfigured.json()["detail"] == "Stripe billing is not configured"

    webhook = client.post("/v1/webhooks/stripe", content=b"{}")
    assert webhook.status_code == 503


def test_subscription_webhook_sync_is_idempotent(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'billing.sqlite3'}", future=True)
    Base.metadata.create_all(engine)
    settings = SimpleNamespace(
        stripe_secret_key="sk_test_value",
        stripe_price_team_monthly="price_team",
        stripe_price_business_monthly="price_business",
    )

    with Session(engine) as session:
        session.add(Tenant(id="tenant_alpha", name="Tenant Alpha"))
        session.commit()
        service = StripeBillingService(session, settings)
        event = {
            "id": "evt_subscription_1",
            "type": "customer.subscription.updated",
            "livemode": False,
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "status": "active",
                    "cancel_at_period_end": False,
                    "current_period_end": 1_800_000_000,
                    "metadata": {
                        "tenant_id": "tenant_alpha",
                        "plan_key": "team",
                    },
                    "items": {"data": [{"price": {"id": "price_team"}}]},
                }
            },
        }
        payload_hash = hashlib.sha256(b"subscription").hexdigest()

        assert service.process_event(event, payload_hash) is False
        assert service.process_event(event, payload_hash) is True

        account = session.scalar(
            select(BillingAccount).where(BillingAccount.tenant_id == "tenant_alpha")
        )
        assert account is not None
        assert account.stripe_customer_id == "cus_123"
        assert account.stripe_subscription_id == "sub_123"
        assert account.plan_key == "team"
        assert account.subscription_status == "active"
        assert "cascade_execution" in account.entitlements

        event_row = session.get(StripeWebhookEvent, "evt_subscription_1")
        assert event_row is not None
        assert event_row.processing_status == "processed"


def test_payment_failure_grace_is_bounded_and_cancellation_revokes_access(
    tmp_path,
    monkeypatch,
):
    engine = create_engine(f"sqlite:///{tmp_path / 'payment-grace.sqlite3'}", future=True)
    Base.metadata.create_all(engine)
    settings = SimpleNamespace(
        stripe_secret_key="sk_test_value",
        stripe_price_team_monthly="price_team",
        stripe_price_business_monthly="price_business",
        billing_past_due_grace_days=3,
    )
    failure_at = datetime(2026, 7, 28, 12, 0, 0, tzinfo=UTC).replace(tzinfo=None)
    monkeypatch.setattr("app.services.billing._utcnow", lambda: failure_at)

    with Session(engine) as session:
        session.add(Tenant(id="tenant_alpha", name="Tenant Alpha"))
        session.commit()
        service = StripeBillingService(session, settings)
        active_subscription = {
            "id": "evt_active",
            "type": "customer.subscription.updated",
            "livemode": False,
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "status": "active",
                    "metadata": {
                        "tenant_id": "tenant_alpha",
                        "plan_key": "team",
                    },
                    "items": {"data": [{"price": {"id": "price_team"}}]},
                }
            },
        }
        service.process_event(active_subscription, "a" * 64)

        failed_invoice = {
            "id": "evt_failed_1",
            "type": "invoice.payment_failed",
            "livemode": False,
            "data": {
                "object": {
                    "id": "in_failed_1",
                    "customer": "cus_123",
                    "subscription": "sub_123",
                }
            },
        }
        service.process_event(failed_invoice, "b" * 64)
        account = session.scalar(
            select(BillingAccount).where(BillingAccount.tenant_id == "tenant_alpha")
        )
        assert account is not None
        assert account.subscription_status == "past_due"
        assert account.payment_grace_ends_at == failure_at + timedelta(days=3)
        assert "api_access" in account.entitlements

        monkeypatch.setattr(
            "app.services.billing._utcnow",
            lambda: failure_at + timedelta(days=2),
        )
        failed_invoice["id"] = "evt_failed_2"
        failed_invoice["data"]["object"]["id"] = "in_failed_2"
        service.process_event(failed_invoice, "c" * 64)
        session.refresh(account)
        assert account.payment_grace_ends_at == failure_at + timedelta(days=3)

        canceled_subscription = {
            "id": "evt_canceled",
            "type": "customer.subscription.deleted",
            "livemode": False,
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "status": "canceled",
                    "metadata": {
                        "tenant_id": "tenant_alpha",
                        "plan_key": "team",
                    },
                    "items": {"data": [{"price": {"id": "price_team"}}]},
                }
            },
        }
        service.process_event(canceled_subscription, "d" * 64)
        session.refresh(account)
        assert account.subscription_status == "canceled"
        assert account.payment_grace_ends_at is None
        assert account.entitlements == []


def test_checkout_uses_allowlisted_price_and_idempotency_key(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'checkout.sqlite3'}", future=True)
    Base.metadata.create_all(engine)
    settings = SimpleNamespace(
        stripe_secret_key="sk_test_value",
        stripe_price_team_monthly="price_team",
        stripe_price_business_monthly="price_business",
        public_web_url="https://salti8.com",
    )

    with Session(engine) as session:
        session.add(Tenant(id="tenant_alpha", name="Tenant Alpha"))
        session.commit()
        service = StripeBillingService(session, settings)
        create = Mock(
            return_value=SimpleNamespace(
                id="cs_test_123",
                url="https://checkout.stripe.com/c/pay/cs_test_123",
            )
        )
        service.client = SimpleNamespace(
            v1=SimpleNamespace(
                checkout=SimpleNamespace(sessions=SimpleNamespace(create=create))
            )
        )

        url, session_id = service.create_checkout_session(
            "tenant_alpha",
            "team",
            "billing@example.com",
            "attempt-1",
        )

        assert url.startswith("https://checkout.stripe.com/")
        assert session_id == "cs_test_123"
        (params,) = create.call_args.args
        options = create.call_args.kwargs["options"]
        assert params["line_items"] == [{"price": "price_team", "quantity": 1}]
        assert params["client_reference_id"] == "tenant_alpha"
        assert params["success_url"].startswith("https://salti8.com/billing/success/")
        assert params["cancel_url"] == (
            "https://salti8.com/pricing/?checkout=cancelled"
        )
        assert options == {"idempotency_key": "checkout:tenant_alpha:attempt-1"}


def test_customer_billing_uses_signed_organization_identity(tmp_path):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    issuer = "https://salti8-test.clerk.accounts.dev"

    client = _build_client(tmp_path / "customer-billing.sqlite3")
    os.environ["CLERK_JWT_KEY"] = public_key
    os.environ["CLERK_ISSUER"] = issuer
    os.environ["CLERK_AUTHORIZED_PARTIES"] = "https://salti8.com"
    _reset_settings()

    tenant = client.post(
        "/admin/tenants",
        headers=_admin_headers(),
        json={
            "tenant_id": "tenant_alpha",
            "name": "Tenant Alpha",
            "clerk_organization_id": "org_alpha",
        },
    )
    assert tenant.status_code == 201

    token = jwt.encode(
        {
            "sub": "user_alpha",
            "org_id": "org_alpha",
            "azp": "https://salti8.com",
            "iss": issuer,
            "iat": int(time.time()),
            "nbf": int(time.time()) - 1,
            "exp": int(time.time()) + 300,
        },
        private_key,
        algorithm="RS256",
    )
    response = client.get(
        "/v1/customer/billing",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["tenant_id"] == "tenant_alpha"
    assert response.json()["plan_key"] == "developer"

    wrong_organization_token = jwt.encode(
        {
            "sub": "user_alpha",
            "org_id": "org_unknown",
            "azp": "https://salti8.com",
            "iss": issuer,
            "iat": int(time.time()),
            "nbf": int(time.time()) - 1,
            "exp": int(time.time()) + 300,
        },
        private_key,
        algorithm="RS256",
    )
    forbidden = client.get(
        "/v1/customer/billing",
        headers={"Authorization": f"Bearer {wrong_organization_token}"},
    )
    assert forbidden.status_code == 403
