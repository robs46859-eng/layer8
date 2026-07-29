# Sandbox services and first-customer activation

SALTI8 can run locally with mock inference, but a complete customer sandbox
uses the following external services.

## Required sandbox accounts

### Clerk development instance

Clerk provides customer sign-in, organization membership, invitations, and
short-lived session tokens.

Web environment:

```text
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The web application is a static browser client and does not use a Clerk
secret key. Never put `CLERK_SECRET_KEY` in Hostinger.

API environment:

```text
CLERK_JWT_KEY=-----BEGIN PUBLIC KEY-----...
CLERK_ISSUER=https://your-instance.clerk.accounts.dev
CLERK_AUTHORIZED_PARTIES=http://localhost:3000,https://salti8.com
```

Copy the PEM public key and issuer from the Clerk API Keys page. Keep sign-up
invitation-only for the private pilot. Enable Organizations and require a
customer to have an active organization before billing access.

### Stripe test mode

Create test-mode Team and Business recurring monthly Prices, enable the
customer portal, and use:

```text
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_LIVE_MODE=false
STRIPE_PRICE_TEAM_MONTHLY=price_...
STRIPE_PRICE_BUSINESS_MONTHLY=price_...
STRIPE_PORTAL_CONFIGURATION_ID=bpc_...
```

Forward Stripe CLI events to:

```text
http://localhost:8000/v1/webhooks/stripe
```

### Platform infrastructure

The self-hosted API expects PostgreSQL, Redis, S3-compatible object storage,
and an SQS-compatible audit queue. The repository's Docker Compose stack
provides local versions. Production uses the managed services declared in
`render.yaml`.

### AI provider

No external model API is required for billing or customer login. The `mock`
provider is the safe sandbox default. Add `OPENAI_API_KEY` only when testing
real routed inference; do not expose it to the web application.

## First customer sequence

1. Create a Clerk Organization for the customer and invite the customer
   administrator by email.
2. Copy the Clerk Organization ID, such as `org_...`.
3. Create the Layer8 tenant with the same organization mapping:

```bash
curl -X POST https://api.salti8.com/admin/tenants \
  -H "Authorization: Bearer ${ADMIN_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant_first_customer",
    "name": "First Customer",
    "clerk_organization_id": "org_..."
  }'
```

4. Create the customer's scoped Layer8 API key through the admin API and
   deliver it through a secure secret-sharing channel.
5. Ask the customer to sign in at `https://salti8.com/sign-in`, select their
   organization, and open Billing & Entitlements.
6. Run a Stripe test Checkout first. Confirm the signed webhook changes the
   account from `inactive` to `active`, grants the expected entitlements, and
   opens the Stripe customer portal.
7. Repeat with live Stripe configuration only after the sandbox path passes.

The customer's first useful engagement should be a narrow paid pilot: one
workflow, one accountable owner, one measurable failure mode, and a 30-day
acceptance plan. Avoid selling a platform-wide transformation before Layer8
has evidence from that first production workflow.
