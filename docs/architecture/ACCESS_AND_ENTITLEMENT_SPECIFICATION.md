# Customer access and entitlement specification

**Product:** Layer8 Adaptive by SALTI8  
**Status:** Current production contract  
**Updated:** July 28, 2026

## 1. Purpose

This specification defines how a person reaches deployment-gated features,
which system owns each authorization decision, and how a platform operator
provisions the first usable customer workspace.

## 2. Non-negotiable distinction

Clerk does not currently grant platform-admin API access.

- Clerk authenticates customer users and supplies organization membership.
- Layer8 maps one Clerk organization to one active tenant.
- Customer routes accept a Clerk session token containing that organization.
- Platform `/admin` routes accept only the separate `ADMIN_API_TOKEN`.
- The deployed website has no platform-admin console.

A Clerk user marked as an organization administrator can manage that customer
organization in Clerk, but cannot call Layer8 platform-admin routes unless the
separate platform credential is deliberately supplied outside the browser.

## 3. Actors

| Actor | Identity | Allowed actions |
| --- | --- | --- |
| Platform operator | Protected operational access plus `ADMIN_API_TOKEN` | Create and update Layer8 tenants, map Clerk organizations, issue/revoke/rotate service API keys, review pilot applications |
| Customer organization administrator | Clerk user with membership in the customer organization | Select the organization, view its billing state, start Checkout, open its Stripe portal |
| Customer member | Clerk user with an allowed organization membership | Access only customer features permitted by current product policy |
| Service client | Layer8 scoped API key | Invoke allowed runtime models and capabilities subject to tenant billing and entitlements |

Clerk organization roles are not yet translated into Layer8 tenant-aware RBAC.
Until that work is implemented, do not describe the website as a platform
administration surface.

## 4. Authorization rules

### 4.1 Customer website

The customer billing screen requires:

1. a loaded Clerk production instance;
2. a signed-in Clerk user;
3. an active Clerk organization selection;
4. a session token containing `org_id`;
5. a valid token issuer and signature;
6. an allowed `azp` value from `CLERK_AUTHORIZED_PARTIES`;
7. exactly one active Layer8 tenant mapped to that Clerk organization ID, or
   `SELF_SERVICE_SIGNUP_ENABLED=true` so the API can create that mapping; and
8. successful API readiness for the backing services needed by the request.

### 4.2 Platform admin API

Every `/admin` request requires:

```text
Authorization: Bearer ${ADMIN_API_TOKEN}
```

The credential must be stored in Render's secret configuration and loaded into
the API service. It must never be placed in Hostinger, committed to Git,
rendered into a web page, pasted into analytics, or sent in a Clerk claim.

### 4.3 Runtime API

Inference uses tenant-scoped Layer8 API keys. The request is also subject to
tenant status, subscription status, required entitlement, model allowlist,
scope, rate limit and policy enforcement.

## 5. First workspace activation

In the public self-service environment, a customer creates a Clerk account,
names a workspace, and selects it. The first authenticated billing request
creates a deterministic Layer8 tenant for the verified Clerk organization. The
customer can then subscribe and, after the signed Stripe webhook grants
`api_access`, create up to two scoped API keys from the billing screen.

Private environments can keep `SELF_SERVICE_SIGNUP_ENABLED=false` and use the
manual activation sequence below.

### Step 1 — restore the production control plane

Require `https://api.salti8.com/readyz` to return `200`. At minimum,
PostgreSQL, Redis, audit storage and the audit queue must report `ok`.

Configure `ADMIN_API_TOKEN` in Render and redeploy. Verify an anonymous request
to `/admin/tenants` returns `401`. A `503` means admin authentication remains
unconfigured.

### Step 2 — create the Clerk organization

In the Clerk production dashboard:

1. create the customer organization;
2. invite the intended customer administrator;
3. ensure Organizations are enabled for the production instance; and
4. copy the stable organization ID beginning with `org_`.

The user currently reaching `Organization required` must be invited to, or
made a member of, this organization before the selector can produce an
`org_id`.

### Step 3 — map the organization to a Layer8 tenant

Load the admin credential into a local terminal without printing it. Then
create a tenant:

```bash
curl --fail-with-body -X POST https://api.salti8.com/admin/tenants \
  -H "Authorization: Bearer ${ADMIN_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant_customer_slug",
    "name": "Customer Name",
    "clerk_organization_id": "org_replace_me"
  }'
```

For an existing tenant, map the organization with:

```bash
curl --fail-with-body -X PATCH \
  https://api.salti8.com/admin/tenants/tenant_customer_slug \
  -H "Authorization: Bearer ${ADMIN_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"clerk_organization_id":"org_replace_me","status":"active"}'
```

One Clerk organization ID may map to only one Layer8 tenant.

### Step 4 — verify customer access

1. Sign in at `https://salti8.com/sign-in/`.
2. Select the newly assigned organization.
3. Open `https://salti8.com/app/billing/`.
4. Confirm the page shows Billing & Entitlements instead of Organization
   required.
5. Confirm the customer billing API returns the mapped tenant's billing state.

### Step 5 — verify entitlements

Use Stripe test mode first:

1. start Checkout from the mapped organization;
2. complete a test payment;
3. verify the signed webhook is accepted;
4. verify the subscription becomes active;
5. verify expected entitlements are displayed; and
6. verify the Stripe customer portal opens for the same tenant.

Browser redirects do not activate access. Only the validated Stripe webhook
may update subscription and entitlement state.

## 6. Current gated surface

The website currently exposes Billing & Entitlements and customer API-key
creation. It does not expose:

- Layer8 platform tenant administration;
- service API-key rotation or revocation;
- provider credential management;
- routing-policy administration;
- the target Layer8 dashboard or playground;
- an audit explorer; or
- pilot-application administration.

Those functions remain API-only or are roadmap items.

## 7. Failure map

| Observed result | Meaning | Correct action |
| --- | --- | --- |
| Billing page says `Create your workspace` | User is signed in, but the session has no active `org_id` | Name a workspace or select an existing one |
| API says `organization is not linked to an active Layer8 tenant` | No active tenant mapping exists and self-service is disabled | Create or patch the mapping, or enable self-service for that environment |
| `/admin/tenants` returns `503` | `ADMIN_API_TOKEN` is absent | Configure the Render secret and redeploy |
| `/admin/tenants` returns `401` without a token | Admin gate is configured and denying anonymous access | Expected result |
| Customer billing returns `401` without a token | Customer auth boundary is live | Expected result |
| Customer billing returns `403` for authorized party | Clerk token came from an unapproved web origin | Correct `CLERK_AUTHORIZED_PARTIES`; do not disable the check |
| `/readyz` returns `503` | One or more required infrastructure dependencies failed | Repair the named dependency before customer activation |
| Checkout succeeds but entitlements remain inactive | Signed webhook did not update the mapped tenant | Verify webhook secret, event mode, tenant metadata and event processing |

## 8. Acceptance tests

Access is correctly provisioned only when:

- an anonymous website visitor cannot see customer billing data;
- an authenticated user without an organization is held at the organization
  gate;
- an authenticated member of an unmapped organization receives a controlled
  `403` when self-service is disabled;
- an authenticated member of an unmapped organization receives one isolated,
  deterministic tenant when self-service is enabled;
- an authenticated member of the mapped active organization receives only
  that tenant's billing state;
- API-key creation requires an active paid state and `api_access`;
- no more than two active customer-created API keys are allowed per tenant;
- a different organization cannot read or mutate the tenant;
- anonymous admin access returns `401`;
- an invalid admin token returns `403`;
- Clerk tokens cannot authorize `/admin`;
- Stripe webhook signatures and live/test mode are validated;
- entitlement changes occur only after validated billing events; and
- `/readyz` is `200` before the release is declared operational.

## 9. Security invariants

- Never expose the platform admin token to the static website.
- Never use a Clerk publishable key as proof of backend authorization.
- Never trust a tenant ID supplied by the customer browser; derive it from the
  signed `org_id` mapping.
- Never treat a successful Checkout redirect as payment confirmation.
- Never weaken `azp`, issuer, signature or organization checks to unblock a
  user.
- Never map one Clerk organization to multiple tenants.
- Never describe liveness as readiness.
