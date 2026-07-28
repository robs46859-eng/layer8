import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from app.schemas.inference import InferenceRequest, Message
from app.services.context import RequestContext
from app.services.entitlements import (
    BillingAccessError,
    EntitlementAccessError,
    has_billing_access,
)
from app.services.policy import PolicyService


def _context() -> RequestContext:
    context = RequestContext.from_request(
        payload=InferenceRequest(
            model="gpt-4.1-mini",
            messages=[Message(role="user", content="hello")],
        ),
        presented_api_key="ak_live_test.secret",
        idempotency_key=None,
        client_host="127.0.0.1",
    )
    context.tenant_id = "tenant_alpha"
    context.api_key_scopes = {"inference:invoke"}
    context.allowed_models = {"gpt-4.1-mini"}
    context.billing_status = "active"
    context.billing_entitlements = {"api_access"}
    return context


def test_active_subscription_with_entitlement_passes_policy():
    context = _context()

    asyncio.run(PolicyService().evaluate(context))

    assert context.policy_snapshot["billing_status"] == "active"
    assert context.policy_snapshot["billing_entitlements"] == ["api_access"]


def test_inactive_subscription_fails_before_inference():
    context = _context()
    context.billing_status = "canceled"

    with pytest.raises(BillingAccessError, match="active subscription"):
        asyncio.run(PolicyService().evaluate(context))


def test_active_subscription_without_entitlement_fails_closed():
    context = _context()
    context.billing_entitlements = set()

    with pytest.raises(EntitlementAccessError, match="api_access"):
        asyncio.run(PolicyService().evaluate(context))


def test_past_due_access_is_bounded_by_grace_period():
    now = datetime(2026, 7, 28, 12, 0, 0, tzinfo=UTC)
    grace_end = now + timedelta(days=3)

    assert has_billing_access("past_due", grace_end, now=now + timedelta(days=2))
    assert not has_billing_access(
        "past_due",
        grace_end,
        now=now + timedelta(days=3, seconds=1),
    )
    assert not has_billing_access("past_due", None, now=now)
