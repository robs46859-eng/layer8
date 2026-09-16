# VirtuaPet integration with Layer8 Adaptive by SALTI8

Updated: September 16, 2026. Responsible organization: SALTI8.

Status: implemented, default off; local test evidence is not deployed-provider evidence.
This release supports short-lived identity proofs and narrow, nonclinical authorization.
It does not enable a clinical digital twin, change a subscription, create a model, or
connect a Pawsome3D/PawPath account automatically.

## Service ownership and trust

Layer8 Adaptive retains customer identity, organization mapping, tenant API keys,
Stripe billing, plan entitlements, and its signing key. VirtuaPet owns its users,
organization membership, one-time linking challenges, consent, provider account links,
and the final resource/ownership check. No service reads another service's database.
An email address, request header, organization administrator role, or matching name is
not proof that two accounts belong to the same person.

The new endpoints are independent of the older internal spatial entitlement bypass.
`ADMIN_API_TOKEN`, `INTERNAL_SPATIAL_TENANT_IDS`, demo API keys, and inference/spatial
scopes cannot substitute for the required integration authentication.

## Endpoints

### POST `/v1/integrations/virtuapet/link-proof`

The caller presents a real Clerk session in `Authorization: Bearer <session>`.
The backend verifies the RS256 signature, issuer, expiration, not-before, issued-at,
subject, allowed `azp`, and organization claim. It requires a pre-existing active tenant
whose `clerk_organization_id` matches the signed session. Unlike customer signup,
this route never provisions a tenant, even if self-service signup is enabled.

JSON body (all four fields required UUID strings; extra fields rejected):

```json
{
  "subject": "11111111-1111-4111-8111-111111111111",
  "tenantId": "22222222-2222-4222-8222-222222222222",
  "challengeId": "33333333-3333-4333-8333-333333333333",
  "nonce": "44444444-4444-4444-8444-444444444444"
}
```

`subject` and `tenantId` identify VirtuaPet's already-authenticated user and organization.
The tenant must match the operator-provisioned VirtuaPet-to-Layer8 tenant map.
VirtuaPet must independently verify that the challenge and nonce belong to that user
and organization, remain unexpired, and have never been consumed. Layer8 signing these
fields does not itself prove the caller owns the corresponding VirtuaPet account.

The response is exactly `{ "proofToken": "<signed JWT>" }` with `Cache-Control: no-store`.
The ES256 JWT header is `alg`, `kid`, and `typ: vp-layer8-link+jwt`. Claims are exactly:

| Claim | Source |
|---|---|
| `iss`, `aud` | Explicit operator-configured issuer and link audience |
| `sub`, `tenantId`, `challengeId`, `nonce` | Validated request context |
| `iat`, `exp`, `jti` | Current time, bounded expiry, new UUID |
| `protocol` | `virtuapet.layer8.link.v1` |
| `providerSubject` | Verified Clerk session subject |
| `providerTenantId` | Existing active Layer8 tenant ID |
| `providerOrganizationId` | Verified Clerk organization ID |

Expiry is the earlier of 300 seconds or the Clerk session expiry. No automatic renewal
is implemented. The first release needs a newly authenticated proof when this evidence
expires; a stored account-link record does not extend a JWT's lifetime. Immediate Clerk
session revocation/introspection is not implemented: removal takes effect no later than
the remaining session/proof lifetime, while Layer8 tenant disablement is checked afresh.

### POST `/v1/integrations/virtuapet/policy`

The caller presents a dedicated Layer8 tenant API key in `Authorization: Bearer <key>`.
The existing hashed key store is read again on every request. Key/tenant status must be
active and the key must include `virtuapet:policy`. A distributed tenant rate limit runs
before proof/policy processing. The endpoint does not accept Clerk sessions as service keys.

The strict request fields are `protocol`, `requestId`, `subject`, `tenantId`,
`correlationId`, `action`, `resource`, `purpose`, `requiredEntitlements`, and `identityProof`.
`protocol` is `virtuapet.layer8.policy.v1`; context IDs are UUIDs. `identityProof` is the
unexpired link JWT above. The signature, exact header/claims, issuer, distinct link
audience, provider tenant, current tenant map, current active Clerk organization binding,
subject and VirtuaPet tenant must all match. A stale or mismatched proof never grants access.

Policy allowlist:

| Action / resource / purpose | Layer8 requirements | Granted VirtuaPet entitlement |
|---|---|---|
| `spatial.preview.read` / `pawsome3d:order:<UUID>` / `owner_visual_preview` | Active billing or existing bounded payment-grace policy, `spatial_intelligence` | `spatial.preview` |
| `pawpath.nearby.read` / `pawpath:user:<same VP subject>` / `user_requested_nearby_search` | Same billing rule, both `api_access` and explicit `pawpath.community` | `pawpath.community` |

Anything else produces a signed denial. Empty `requiredEntitlements` cannot relax this
allowlist. Extra requested entitlements deny access. `api_access` alone does not grant
PawPath; current standard plans do not grant `pawpath.community` by default. An explicit
commercial entitlement decision is required before adding it to the existing billing
source of truth; this integration does not modify plans or Stripe products.

The response is exactly `{ "decisionToken": "<signed JWT>" }`. Its `typ` is
`vp-layer8-policy+jwt`; exact claims are `iss`, `aud`, `sub`, `iat`, `exp`, `jti`,
`protocol`, `tenantId`, `correlationId`, `requestId`, `action`, `resource`, `purpose`,
`policyVersion`, `outcome`, `entitlements`, and `obligations`. Decisions expire within
60 seconds and never outlive the identity proof. Obligations are an empty array.
Denied decisions have no entitlements. Invalid authentication/proof is an HTTP error,
not a signed allow/deny response.

Every request uses a fresh unpredictable UUID `requestId`. The provider reserves it
atomically per tenant for 300 seconds. Reusing it returns 409; retries must use a new
request ID and verify a newly bound response. The identity proof may authorize several
distinct requests during its short lifetime. Single-use account-link consumption is a
separate VirtuaPet database transaction, not a property of this policy endpoint.

These are subscription/policy checks, not proof of order ownership or access to nearby
people. VirtuaPet must still enforce its active membership, linked provider identity,
consent, order allowlist and delegated provider access. No direct signed-URL asset
download or medical permission is granted by Layer8.

## Operator configuration (no real credentials in Git)

| Layer8 setting | Required value or constraint |
|---|---|
| `VIRTUAPET_INTEGRATION_ENABLED` | Defaults `false`; enable only after trust/configuration review |
| `VIRTUAPET_SIGNING_PRIVATE_KEY` | P-256 PKCS8 PEM provided through a managed secret reference; never a browser value |
| `VIRTUAPET_SIGNING_KEY_ID` | Unique key version ID pinned by VirtuaPet |
| `VIRTUAPET_POLICY_ISSUER` | Stable exact issuer shared with VirtuaPet; no implicit deployment host |
| `VIRTUAPET_POLICY_AUDIENCE` | Policy audience, e.g. `virtuapet-policy` |
| `VIRTUAPET_LINK_AUDIENCE` | Different link audience, e.g. `virtuapet-links` |
| `VIRTUAPET_TENANT_MAP_JSON` | Explicit JSON object mapping canonical VP organization UUIDs to real Layer8 tenant IDs |
| `VIRTUAPET_RATE_LIMIT_PER_MINUTE` | Default 60, range 1–600, per tenant per endpoint |
| `CLERK_JWT_KEY`, `CLERK_ISSUER`, `CLERK_AUTHORIZED_PARTIES` | Existing verified Clerk configuration; no empty/wildcard authorized-party list |
| `BACKEND_MODE`, `DATABASE_URL` | `self_hosted` and PostgreSQL in staging/production |
| `REDIS_URL` | Reachable managed Redis with operational retention/security controls |

This release loads an exportable signing key through the managed secret environment
for nonclinical staging. It does not implement direct Azure Key Vault/HSM remote-signing
operations. Do not claim hardware-backed non-exportable signing. No key is generated by
the application and no private key/JWT is committed. Key rotation requires coordinated
public-key pinning in VirtuaPet, then Layer8 key/kid replacement; existing five-minute
proofs under the old key fail closed after replacement and require relinking.

Provision a **dedicated** key using the existing admin API's tenant-scoped key creation,
`POST /admin/tenants/<real-tenant-id>/api-keys`, with body
`{"scopes":["virtuapet:policy"],"allowed_models":[]}`. This provisioning call uses the
existing admin authorization; the resulting tenant key is the runtime credential.
Never configure the admin token itself as VirtuaPet's service token. Store each tenant's
key in the relevant server-side secret manager; rotation/revocation uses existing admin APIs.

Transfer only the public P-256 JWK (`kty`, `crv`, `x`, `y`, `kid`, `alg: ES256`, `use: sig`)
to VirtuaPet's pinned JWKS configuration. There is no open dynamic key-discovery URL
in this release. Compare public key fingerprints through the operator-controlled channel.
If a browser calls link-proof directly, explicitly configure that trusted browser origin
in CORS and Clerk authorized parties. Do not add wildcards to resolve a failed CORS check.

## Failure handling, audit, and readiness

Missing settings, wrong signing key, missing PostgreSQL, or Redis failure cause 503.
Missing/invalid credentials or disabled keys cause 401; tenant/proof/scope mismatch
causes 403; replay causes 409; malformed body causes 422; size over 32 KiB causes 413;
rate exhaustion causes 429. All integration responses disable caching. Validation and
unexpected errors are reduced to safe codes instead of returning inputs, SQL text or JWTs.

Redis Lua increments and sets a 60-second expiry atomically; replay protection uses
`SET NX EX 300`. Both fail closed during Redis faults. In-memory substitutes are permitted
only in explicit `dev`, `development`, or `test`, never staging or production. Database
authentication reads are not cached. No live data migrations are needed in Layer8.

Process logs contain a policy decision UUID, outcome, policy version and event name.
They deliberately omit tokens, provider subjects, order IDs, nonce and request bodies.
This is limited security telemetry, **not a durable audit ledger**. Operational log retention,
durable governance audit, immediate identity revocation and workload scaling evidence remain
activation/production-hardening work. Do not call this clinically production-ready.

## Test and deployment acceptance

Run `.venv/bin/pytest -q tests/test_virtuapet.py` and the full existing test suite plus Ruff.
Tests use disposable SQLite rows and freshly generated test-only signing/Clerk keys.
They exercise real FastAPI routes and cryptographic JWTs, stored-key hashes, no provisioning,
wrong issuer/party/organization/signature/expiry, explicit scope, fresh cancellation/revocation,
no internal-spatial bypass, action allowlist, duplicate request IDs, tenant changes, proof-bound
expiry, sanitized errors and Redis failure behavior. Redis unit stubs prove call behavior,
not live distributed-service availability. Cross-language VirtuaPet verification is a separate gate.

Before activation:

1. Deploy the reviewed image with the feature disabled and retain the previous immutable image.
2. Confirm the existing Layer8 PostgreSQL, Redis and readiness checks are healthy.
3. Provision an approved tenant map, managed signing secret, public pins and restricted tenant keys.
4. Authenticate one real test user separately in both systems and consume a fresh VP challenge once.
5. Prove successful policy verification, changed-subject/tenant denial, revoked consent denial,
   billing cancellation denial, expired proof denial, API-key revocation and Redis-outage denial.
6. Complete provider-specific Pawsome3D/PawPath account ownership, consent and resource tests.
7. Record exact image/commit IDs and fresh external results before claiming a connected deployment.

Rollback: turn the integration feature off, revoke its dedicated tenant service keys if needed,
and return to the previous immutable image. Existing Stripe customer billing and other routes
remain separate. Do not roll back the entire customer database or rewrite Git history.
