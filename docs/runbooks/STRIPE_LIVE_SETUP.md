# Stripe live setup

Layer8 Adaptive uses Stripe-hosted Checkout for subscriptions, the Stripe
customer portal for self-service billing, and signed webhooks as the
authoritative source for access changes.

## Public endpoints

- Checkout creation: `POST https://api.salti8.com/v1/billing/checkout`
- Customer portal: `POST https://api.salti8.com/v1/billing/portal`
- Billing status: `GET https://api.salti8.com/v1/billing/{tenant_id}`
- Customer billing status: `GET https://api.salti8.com/v1/customer/billing`
- Customer Checkout: `POST https://api.salti8.com/v1/customer/billing/checkout`
- Customer portal: `POST https://api.salti8.com/v1/customer/billing/portal`
- Stripe webhook: `POST https://api.salti8.com/v1/webhooks/stripe`
- Checkout return page: `https://salti8.com/billing/success`

Checkout, portal, and billing-status endpoints require authenticated control
plane access. The webhook does not use bearer authentication; it requires and
verifies Stripe's `Stripe-Signature` header against the environment-specific
webhook signing secret.

The `/v1/customer/billing` endpoints accept a short-lived Clerk session token.
The API verifies its signature, issuer, expiration, and authorized party, then
maps the active Clerk organization to a Layer8 tenant. The browser never sends
or chooses a tenant ID.

## Required live configuration

Set these values in the production secret manager or deployment environment.
Never commit them:

```text
PUBLIC_WEB_URL=https://salti8.com
PUBLIC_API_URL=https://api.salti8.com
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_LIVE_MODE=true
STRIPE_PRICE_TEAM_MONTHLY=price_...
STRIPE_PRICE_BUSINESS_MONTHLY=price_...
STRIPE_PORTAL_CONFIGURATION_ID=bpc_...
CLERK_JWT_KEY=-----BEGIN PUBLIC KEY-----...
CLERK_ISSUER=https://your-instance.clerk.accounts.dev
CLERK_AUTHORIZED_PARTIES=https://salti8.com
```

Create recurring monthly Prices in the live Stripe account and place their
Price IDs in the matching variables. The backend accepts only these allowlisted
plans; clients cannot submit arbitrary Stripe Price IDs.

## Webhook listeners

Configure the live Stripe webhook endpoint to send only:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`
- `checkout.session.async_payment_failed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `customer.subscription.trial_will_end`
- `invoice.paid`
- `invoice.payment_failed`
- `invoice.payment_action_required`
- `entitlements.active_entitlement_summary.updated`

`customer.subscription.*` is authoritative for subscription lifecycle.
`invoice.paid` renews paid access, and failed/action-required invoice events
place the billing account into `past_due`. The entitlement summary event can
replace the local feature list when Stripe Billing Entitlements is configured.

## Stripe Dashboard sequence

1. Switch the Stripe Dashboard to live mode.
2. Create the SALTI8 products and recurring Prices.
3. Configure product features in Stripe Billing Entitlements if used.
4. Configure and activate a customer portal configuration.
5. Add `https://api.salti8.com/v1/webhooks/stripe` as a webhook destination.
6. Select the listeners listed above; do not subscribe to every event.
7. Copy the destination's live `whsec_...` secret into the production secret
   manager.
8. Set live Price IDs and `STRIPE_LIVE_MODE=true`.
9. Run database migration `20260728_0003`.
10. Complete one live low-value subscription with an approved test tenant,
    confirm the billing account becomes `active`, open the customer portal,
    then cancel/refund according to the test plan.

Before the customer can check out, link their Clerk organization to the tenant
through the admin API's `clerk_organization_id` field.

Browser redirects are not proof of payment. Provisioning happens only after a
verified webhook is processed and recorded in `stripe_webhook_events`.

## Local verification

Use Stripe CLI test mode:

```text
stripe listen --forward-to localhost:8000/v1/webhooks/stripe
```

Place the CLI-provided `whsec_...` value in the local environment and leave
`STRIPE_LIVE_MODE=false`. Use test Price IDs and Stripe test cards. Live keys
must never be used on a developer workstation or in automated tests.
