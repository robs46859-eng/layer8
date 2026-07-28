import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import stripe
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import BillingAccount, StripeWebhookEvent, Tenant

logger = logging.getLogger(__name__)

ACTIVE_SUBSCRIPTION_STATUSES = {"active", "trialing"}

PLAN_ENTITLEMENTS = {
    "developer": ["community_support"],
    "team": [
        "api_access",
        "cascade_execution",
        "audit_export",
        "provider_routing",
        "team_support",
    ],
    "business": [
        "api_access",
        "cascade_execution",
        "audit_export",
        "provider_routing",
        "extended_retention",
        "priority_support",
        "sso",
        "spatial_intelligence",
    ],
}

HANDLED_STRIPE_EVENTS = {
    "checkout.session.completed",
    "checkout.session.async_payment_succeeded",
    "checkout.session.async_payment_failed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "customer.subscription.trial_will_end",
    "invoice.paid",
    "invoice.payment_failed",
    "invoice.payment_action_required",
    "entitlements.active_entitlement_summary.updated",
}


def _unix_datetime(value: int | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromtimestamp(value, tz=UTC).replace(tzinfo=None)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _object_id(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("id")
    return getattr(value, "id", None)


class StripeBillingService:
    def __init__(self, session: Session, settings: Settings):
        self.session = session
        self.settings = settings
        self.client = stripe.StripeClient(settings.stripe_secret_key or "sk_test_unconfigured")

    def _require_stripe(self) -> None:
        if not self.settings.stripe_secret_key:
            raise RuntimeError("Stripe billing is not configured")

    def _price_for_plan(self, plan_key: str) -> str:
        prices = {
            "team": self.settings.stripe_price_team_monthly,
            "business": self.settings.stripe_price_business_monthly,
        }
        price_id = prices.get(plan_key)
        if not price_id:
            raise ValueError(f"Stripe price is not configured for plan: {plan_key}")
        return price_id

    def _plan_for_price(self, price_id: str | None) -> str:
        if price_id and price_id == self.settings.stripe_price_team_monthly:
            return "team"
        if price_id and price_id == self.settings.stripe_price_business_monthly:
            return "business"
        return "developer"

    def _billing_account_for_tenant(self, tenant_id: str) -> BillingAccount:
        tenant = self.session.get(Tenant, tenant_id)
        if tenant is None:
            raise ValueError("tenant not found")
        account = self.session.scalar(
            select(BillingAccount).where(BillingAccount.tenant_id == tenant_id)
        )
        if account is None:
            account = BillingAccount(
                id=f"bill_{uuid.uuid4().hex}",
                tenant_id=tenant_id,
                plan_key="developer",
                subscription_status="inactive",
                entitlements=PLAN_ENTITLEMENTS["developer"],
            )
            self.session.add(account)
            self.session.flush()
        return account

    def create_checkout_session(
        self,
        tenant_id: str,
        plan_key: str,
        customer_email: str | None,
        idempotency_key: str,
    ) -> tuple[str, str]:
        self._require_stripe()
        if not idempotency_key or len(idempotency_key) > 255:
            raise ValueError("a valid Idempotency-Key header is required")

        account = self._billing_account_for_tenant(tenant_id)
        price_id = self._price_for_plan(plan_key)
        params: dict[str, Any] = {
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": (
                f"{self.settings.public_web_url.rstrip('/')}/billing/success"
                "?session_id={CHECKOUT_SESSION_ID}"
            ),
            "cancel_url": f"{self.settings.public_web_url.rstrip('/')}/pricing?checkout=cancelled",
            "client_reference_id": tenant_id,
            "allow_promotion_codes": True,
            "billing_address_collection": "auto",
            "metadata": {"tenant_id": tenant_id, "plan_key": plan_key},
            "subscription_data": {
                "metadata": {"tenant_id": tenant_id, "plan_key": plan_key}
            },
        }
        if account.stripe_customer_id:
            params["customer"] = account.stripe_customer_id
        elif customer_email:
            params["customer_email"] = customer_email

        session = self.client.v1.checkout.sessions.create(
            params,
            options={"idempotency_key": f"checkout:{tenant_id}:{idempotency_key}"},
        )
        if not session.url:
            raise RuntimeError("Stripe did not return a Checkout URL")
        self.session.commit()
        return session.url, session.id

    def create_portal_session(self, tenant_id: str) -> str:
        self._require_stripe()
        account = self._billing_account_for_tenant(tenant_id)
        if not account.stripe_customer_id:
            raise ValueError("tenant has no Stripe customer")
        params: dict[str, Any] = {
            "customer": account.stripe_customer_id,
            "return_url": f"{self.settings.public_web_url.rstrip('/')}/app/billing",
        }
        if self.settings.stripe_portal_configuration_id:
            params["configuration"] = self.settings.stripe_portal_configuration_id
        portal = self.client.v1.billing_portal.sessions.create(params)
        self.session.commit()
        return portal.url

    def get_billing_account(self, tenant_id: str) -> BillingAccount:
        return self._billing_account_for_tenant(tenant_id)

    def process_event(self, event: dict[str, Any], payload_sha256: str) -> bool:
        event_id = event["id"]
        event_type = event["type"]
        livemode = bool(event.get("livemode"))

        existing = self.session.get(StripeWebhookEvent, event_id)
        if existing and existing.processing_status == "processed":
            return True

        if existing is None:
            existing = StripeWebhookEvent(
                stripe_event_id=event_id,
                event_type=event_type,
                livemode=livemode,
                payload_sha256=payload_sha256,
                processing_status="processing",
            )
            self.session.add(existing)
            try:
                self.session.commit()
            except IntegrityError:
                self.session.rollback()
                existing = self.session.get(StripeWebhookEvent, event_id)
                if existing and existing.processing_status == "processed":
                    return True
        else:
            existing.processing_status = "processing"
            existing.last_error = None
            self.session.commit()

        try:
            if event_type in HANDLED_STRIPE_EVENTS:
                self._dispatch(event_type, event["data"]["object"])
            else:
                logger.info({"event": "stripe_event_ignored", "stripe_event_type": event_type})
            event_record = self.session.get(StripeWebhookEvent, event_id)
            if event_record:
                event_record.processing_status = "processed"
                event_record.processed_at = _utcnow()
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            event_record = self.session.get(StripeWebhookEvent, event_id)
            if event_record:
                event_record.processing_status = "failed"
                event_record.last_error = str(exc)[:2000]
                self.session.commit()
            raise
        return False

    def _dispatch(self, event_type: str, obj: dict[str, Any]) -> None:
        if event_type.startswith("checkout.session."):
            self._sync_checkout(event_type, obj)
        elif event_type.startswith("customer.subscription."):
            self._sync_subscription(obj)
        elif event_type.startswith("invoice."):
            self._sync_invoice(event_type, obj)
        elif event_type == "entitlements.active_entitlement_summary.updated":
            self._sync_entitlements(obj)

    def _account_by_stripe_ids(
        self, customer_id: str | None, subscription_id: str | None
    ) -> BillingAccount | None:
        clauses = []
        if customer_id:
            clauses.append(BillingAccount.stripe_customer_id == customer_id)
        if subscription_id:
            clauses.append(BillingAccount.stripe_subscription_id == subscription_id)
        if not clauses:
            return None
        return self.session.scalar(select(BillingAccount).where(or_(*clauses)))

    def _sync_checkout(self, event_type: str, obj: dict[str, Any]) -> None:
        metadata = obj.get("metadata") or {}
        tenant_id = obj.get("client_reference_id") or metadata.get("tenant_id")
        if not tenant_id:
            raise ValueError("Stripe Checkout Session is missing tenant metadata")
        account = self._billing_account_for_tenant(tenant_id)
        account.stripe_customer_id = _object_id(obj.get("customer"))
        account.stripe_subscription_id = _object_id(obj.get("subscription"))
        plan_key = metadata.get("plan_key")
        if plan_key in PLAN_ENTITLEMENTS:
            account.plan_key = plan_key
        if event_type == "checkout.session.async_payment_failed":
            self._apply_subscription_access(account, "past_due", account.plan_key)
        account.updated_at = _utcnow()

    def _apply_subscription_access(
        self,
        account: BillingAccount,
        status: str,
        plan_key: str,
    ) -> None:
        previous_status = account.subscription_status
        account.subscription_status = status
        if status in ACTIVE_SUBSCRIPTION_STATUSES:
            account.entitlements = PLAN_ENTITLEMENTS.get(plan_key, [])
            account.payment_grace_ends_at = None
            return
        if status == "past_due":
            if previous_status != "past_due" or account.payment_grace_ends_at is None:
                grace_days = int(
                    getattr(self.settings, "billing_past_due_grace_days", 3)
                )
                account.payment_grace_ends_at = _utcnow() + timedelta(days=grace_days)
            account.entitlements = PLAN_ENTITLEMENTS.get(plan_key, [])
            return
        account.entitlements = []
        account.payment_grace_ends_at = None

    def _sync_subscription(self, obj: dict[str, Any]) -> None:
        metadata = obj.get("metadata") or {}
        tenant_id = metadata.get("tenant_id")
        customer_id = _object_id(obj.get("customer"))
        subscription_id = obj.get("id")
        account = (
            self._billing_account_for_tenant(tenant_id)
            if tenant_id
            else self._account_by_stripe_ids(customer_id, subscription_id)
        )
        if account is None:
            raise ValueError("subscription cannot be associated with a tenant")

        items = (obj.get("items") or {}).get("data") or []
        price_id = None
        period_end = obj.get("current_period_end")
        if items:
            price_id = _object_id(items[0].get("price") or {})
            period_end = period_end or items[0].get("current_period_end")

        status = obj.get("status") or "inactive"
        plan_key = metadata.get("plan_key") or self._plan_for_price(price_id)
        account.stripe_customer_id = customer_id
        account.stripe_subscription_id = subscription_id
        account.stripe_price_id = price_id
        account.plan_key = plan_key
        self._apply_subscription_access(account, status, plan_key)
        account.cancel_at_period_end = bool(obj.get("cancel_at_period_end"))
        account.current_period_end = _unix_datetime(period_end)
        account.updated_at = _utcnow()

    def _sync_invoice(self, event_type: str, obj: dict[str, Any]) -> None:
        customer_id = _object_id(obj.get("customer"))
        subscription_id = _object_id(obj.get("subscription"))
        parent = obj.get("parent") or {}
        subscription_details = parent.get("subscription_details") or {}
        subscription_id = subscription_id or _object_id(
            subscription_details.get("subscription")
        )
        account = self._account_by_stripe_ids(customer_id, subscription_id)
        if account is None:
            logger.warning(
                {
                    "event": "stripe_invoice_unmatched",
                    "invoice_id": obj.get("id"),
                    "customer_id": customer_id,
                }
            )
            return
        account.last_invoice_id = obj.get("id")
        if event_type == "invoice.paid":
            self._apply_subscription_access(account, "active", account.plan_key)
        elif event_type in {"invoice.payment_failed", "invoice.payment_action_required"}:
            self._apply_subscription_access(account, "past_due", account.plan_key)
        account.updated_at = _utcnow()

    def _sync_entitlements(self, obj: dict[str, Any]) -> None:
        customer_id = _object_id(obj.get("customer"))
        account = self._account_by_stripe_ids(customer_id, None)
        if account is None:
            return
        active = obj.get("active_entitlements") or []
        lookup_keys = [
            item.get("lookup_key")
            for item in active
            if isinstance(item, dict) and item.get("lookup_key")
        ]
        if lookup_keys:
            account.entitlements = sorted(set(lookup_keys))
            account.updated_at = _utcnow()
