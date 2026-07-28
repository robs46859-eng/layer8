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
from app.schemas.billing import (
    BillingAccountResponse,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CustomerCheckoutSessionRequest,
    CustomerPortalRequest,
    CustomerPortalResponse,
    StripeWebhookResponse,
)
from app.services.billing import StripeBillingService

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
