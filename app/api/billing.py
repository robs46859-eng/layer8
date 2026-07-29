import hashlib
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db_session,
    require_admin_auth,
    require_customer_tenant,
)
from app.core.config import get_settings
from app.db.models import Tenant
from app.schemas.admin import APIKeyCreateResponse, APIKeyResponse
from app.schemas.billing import (
    BillingAccountResponse,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CustomerCheckoutSessionRequest,
    CustomerPortalRequest,
    CustomerPortalResponse,
    StripeWebhookResponse,
)
from app.services.api_keys import APIKeyAdminService
from app.services.billing import StripeBillingService
from app.services.entitlements import (
    BillingAccessError,
    EntitlementAccessError,
    enforce_entitlement,
)

billing_router = APIRouter(
    prefix="/v1/billing",
    tags=["billing"],
    dependencies=[Depends(require_admin_auth)],
)
stripe_webhook_router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])
customer_billing_router = APIRouter(prefix="/v1/customer/billing", tags=["customer-billing"])

DbSession = Annotated[Session, Depends(get_db_session)]
IdempotencyKey = Annotated[
    str | None, Header(alias="Idempotency-Key")
]
StripeSignature = Annotated[
    str | None, Header(alias="Stripe-Signature")
]
CustomerTenant = Annotated[Tenant, Depends(require_customer_tenant)]


@billing_router.post("/checkout", response_model=CheckoutSessionResponse)
def create_checkout_session(
    payload: CheckoutSessionRequest,
    session: DbSession,
    idempotency_key: IdempotencyKey = None,
) -> CheckoutSessionResponse:
    service = StripeBillingService(session, get_settings())
    try:
        url, session_id = service.create_checkout_session(
            payload.tenant_id,
            payload.plan_key,
            str(payload.customer_email) if payload.customer_email else None,
            idempotency_key or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return CheckoutSessionResponse(checkout_url=url, session_id=session_id)


@billing_router.post("/portal", response_model=CustomerPortalResponse)
def create_customer_portal(
    payload: CustomerPortalRequest,
    session: DbSession,
) -> CustomerPortalResponse:
    service = StripeBillingService(session, get_settings())
    try:
        url = service.create_portal_session(payload.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return CustomerPortalResponse(portal_url=url)


@billing_router.get("/{tenant_id}", response_model=BillingAccountResponse)
def get_billing_account(
    tenant_id: str,
    session: DbSession,
) -> BillingAccountResponse:
    service = StripeBillingService(session, get_settings())
    try:
        account = service.get_billing_account(tenant_id)
        session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BillingAccountResponse.model_validate(account, from_attributes=True)


@customer_billing_router.get("", response_model=BillingAccountResponse)
def get_customer_billing_account(
    tenant: CustomerTenant,
    session: DbSession,
) -> BillingAccountResponse:
    account = StripeBillingService(session, get_settings()).get_billing_account(tenant.id)
    session.commit()
    return BillingAccountResponse.model_validate(account, from_attributes=True)


def _customer_api_key_response(api_key) -> APIKeyResponse:
    return APIKeyResponse.model_validate(api_key, from_attributes=True)


def _require_api_key_entitlement(account) -> None:
    try:
        enforce_entitlement(
            subscription_status=account.subscription_status,
            payment_grace_ends_at=account.payment_grace_ends_at,
            entitlements=set(account.entitlements or []),
            required_entitlement="api_access",
        )
    except BillingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(exc),
        ) from exc
    except EntitlementAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@customer_billing_router.get("/api-keys", response_model=list[APIKeyResponse])
def list_customer_api_keys(
    tenant: CustomerTenant,
    session: DbSession,
) -> list[APIKeyResponse]:
    account = StripeBillingService(session, get_settings()).get_billing_account(tenant.id)
    _require_api_key_entitlement(account)
    keys = APIKeyAdminService(session).list_api_keys(tenant.id)
    return [_customer_api_key_response(api_key) for api_key in keys]


@customer_billing_router.post(
    "/api-keys",
    response_model=APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_api_key(
    tenant: CustomerTenant,
    session: DbSession,
) -> APIKeyCreateResponse:
    account = StripeBillingService(session, get_settings()).get_billing_account(tenant.id)
    _require_api_key_entitlement(account)
    service = APIKeyAdminService(session)
    active_keys = [key for key in service.list_api_keys(tenant.id) if key.status == "active"]
    if len(active_keys) >= 2:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="revoke an existing API key before creating another",
        )
    scopes = ["inference:invoke"]
    if "spatial_intelligence" in set(account.entitlements or []):
        scopes.append("spatial:invoke")
    api_key, raw_key = service.create_api_key(tenant.id, scopes, [])
    payload = _customer_api_key_response(api_key).model_dump()
    return APIKeyCreateResponse(**payload, api_key=raw_key)


@customer_billing_router.post("/checkout", response_model=CheckoutSessionResponse)
def create_customer_checkout_session(
    payload: CustomerCheckoutSessionRequest,
    tenant: CustomerTenant,
    session: DbSession,
    idempotency_key: IdempotencyKey = None,
) -> CheckoutSessionResponse:
    service = StripeBillingService(session, get_settings())
    try:
        url, session_id = service.create_checkout_session(
            tenant.id,
            payload.plan_key,
            str(payload.customer_email) if payload.customer_email else None,
            idempotency_key or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return CheckoutSessionResponse(checkout_url=url, session_id=session_id)


@customer_billing_router.post("/portal", response_model=CustomerPortalResponse)
def create_customer_portal_session(
    tenant: CustomerTenant,
    session: DbSession,
) -> CustomerPortalResponse:
    service = StripeBillingService(session, get_settings())
    try:
        url = service.create_portal_session(tenant.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return CustomerPortalResponse(portal_url=url)


@stripe_webhook_router.post("/stripe", response_model=StripeWebhookResponse)
async def stripe_webhook(
    request: Request,
    session: DbSession,
    stripe_signature: StripeSignature = None,
) -> StripeWebhookResponse:
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhook is not configured",
        )
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="missing Stripe-Signature header",
        )

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.stripe_webhook_secret,
        )
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid Stripe webhook signature",
        ) from exc

    event_dict = event.to_dict_recursive()
    if bool(event_dict.get("livemode")) != settings.stripe_live_mode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe event mode does not match this environment",
        )

    service = StripeBillingService(session, settings)
    duplicate = service.process_event(
        event_dict,
        hashlib.sha256(payload).hexdigest(),
    )
    return StripeWebhookResponse(
        duplicate=duplicate,
        event_type=event_dict["type"],
    )
