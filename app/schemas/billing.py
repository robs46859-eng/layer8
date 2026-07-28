from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CheckoutSessionRequest(BaseModel):
    tenant_id: str = Field(min_length=3, max_length=64)
    plan_key: str = Field(pattern="^(team|business)$")
    customer_email: EmailStr | None = None


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str


class CustomerPortalRequest(BaseModel):
    tenant_id: str = Field(min_length=3, max_length=64)


class CustomerCheckoutSessionRequest(BaseModel):
    plan_key: str = Field(pattern="^(team|business)$")
    customer_email: EmailStr | None = None


class CustomerPortalResponse(BaseModel):
    portal_url: str


class BillingAccountResponse(BaseModel):
    tenant_id: str
    plan_key: str
    subscription_status: str
    cancel_at_period_end: bool
    current_period_end: datetime | None
    entitlements: list[str]


class StripeWebhookResponse(BaseModel):
    received: bool = True
    duplicate: bool = False
    event_type: str
