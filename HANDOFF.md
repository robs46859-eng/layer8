# Layer8 Adaptive Integration Handoff


## Cutover update — 2026-09-17

The authorized production API cutover is in progress. Hostinger now publishes
the Azure ownership TXT record and points `api.salti8.com` at the Azure
Container Apps hostname. Azure accepted the custom hostname and began issuing
managed certificate `mc-managedenviron-api-salti8-com-2877`. Do not mark the
cutover complete until managed TLS and the public health, readiness, CORS, and
signed-webhook probes pass.

Layer8 runs image `ghcr.io/robs46859-eng/layer8:sha-7c77566`. Stripe live
secrets are attached through Key Vault references, live mode is enabled, and a
fresh signed live-mode synthetic event returned HTTP 200; an unsigned event
returned HTTP 400. Real Checkout, subscription, cancellation, portal, and
entitlement lifecycle tests remain open. See
`docs/STATUS_AND_REMAINING_PHASES_2026-09-17.md` for the numbered activation
checklist and remaining phases.

## Production-readiness status — 2026-09-17

Latest activation checkpoint: Azure revision `layer8-staging-api--browsercors`
receives 100% of staging traffic and includes the explicit VirtuaPet UUID to
Layer8 tenant map. Entra guests `rob@virtuapet.com` and
`robs46859@gmail.com` have accepted their invitations. VirtuaPet Staging A is
`62335dff-756b-47a7-ba94-95e240c3680d`; VirtuaPet Staging B is
`6d8bed91-b840-4884-9ecb-907b4cf0c65f`. Each tenant has a distinct
`virtuapet:policy` API key stored only in VirtuaPet Key Vault. No raw key is
recorded here.

Stripe is confirmed in live mode. Existing active catalog entries are SALTI8
Team at $99/month (`price_1TyIL16X8IBUtLKflisiPVqI`) and SALTI8 Business at
$299/month (`price_1TyILs6X8IBUtLKf5HDS6fVs`). Customer portal configuration
`bpc_1TDTW96X8IBUtLKfZd4HKkRk` is active. Webhook destination
`we_1TyGny6X8IBUtLKfRnuQQCpE` is active and listens for all 11 required events.
The live secret key and webhook signing secret are attached through Key Vault references. A signed live-mode synthetic webhook returns HTTP 200, while an unsigned request returns HTTP 400.

Layer8 now runs revision `layer8-staging-api--browsercors` from immutable image
`ghcr.io/robs46859-eng/layer8:sha-7c77566` at 100% traffic. GitHub CI and image
publication run `35230299072` passed for the Stripe SDK compatibility fix.
Fresh `/healthz` and `/readyz`
probes returned 200; PostgreSQL, Redis, Blob Storage, and Service Bus were all
`ok`. The scheduled audit worker uses the same image, and manual execution
`layer8-audit-worker-stcpf04` succeeded.

The SALTI8 Development Clerk issuer and its Key Vault-backed public verifier
are attached to the candidate revision. Clerk confirms one member in each
organization: `rob@virtuapet.com` in SALTI8 Staging A and
`robs46859@gmail.com` in SALTI8 Staging B. The active server-owned mappings are:

| Clerk organization | Layer8 tenant |
| --- | --- |
| `org_3JROrehaWBgw8CD22AWEcyHPWI4` | `salti8-staging-a` |
| `org_3JROvg2ieivvKt1IrGexqN0tcMQ` | `salti8-staging-b` |

These Layer8 tenant IDs are not VirtuaPet organization UUIDs. VirtuaPet keeps
Microsoft Entra authentication. Clerk is used only for SALTI8/Layer8 customer
identity, and Layer8 accepts Clerk v2 `o.id` or legacy `org_id` only after JWT
verification.

### Remaining production-readiness checklist

- [x] Passing CI built and published the immutable Layer8 candidate image.
- [x] Azure staging health, dependency readiness, managed identity, queue,
  audit storage, worker execution, authorization-denial, and rollback evidence
  are recorded.
- [x] The Clerk Development issuer and public verifier are configured on the
  candidate; the verifier stays in Key Vault.
- [x] Two separate Clerk users belong to two separate organizations, each
  mapped to one active Layer8 tenant.
- [x] Exact-origin CORS accepts `https://salti8.com` and rejects an untrusted
  origin; missing and malformed customer sessions fail with 401.
- [ ] Deploy or designate a SALTI8 Development web origin using the Development
  publishable key and candidate API URL, then add that exact origin to CORS and
  `CLERK_AUTHORIZED_PARTIES`. Do not use a wildcard.
- [ ] Sign in as each staging user, select the assigned organization, and retain
  one authenticated browser session per organization.
- [ ] Prove each session can access only its mapped Layer8 tenant and that both
  cross-tenant requests fail. Include session expiry, membership removal, and
  key revocation checks.
- [x] Map the two canonical VirtuaPet organization UUIDs to their approved
  Layer8 tenants, create distinct API keys scoped exactly to
  `virtuapet:policy`, and store them only in VirtuaPet's server-side Key Vault.
- [ ] With both integration enable flags still off, rehearse fresh Entra-backed
  VirtuaPet link challenges, one-time consumption, correct-tenant policy
  decisions, changed-subject/tenant denial, consent revocation, billing
  cancellation, expired proof, replay, API-key revocation, and Redis-outage
  failure.
- [x] Save the 11-event live Stripe webhook selection.
- [ ] Store the Stripe live secret and webhook secret in Key Vault and wire the
  verified live Price IDs and portal configuration; then
  pass signed webhook acceptance, unsigned rejection, Checkout, entitlement,
  cancellation, and customer-portal tests against the Azure candidate.
- [ ] Run a real provider inference for each tenant through the customer API and
  verify database usage, Service Bus delivery, worker completion, and tenant-
  isolated Blob audit evidence. The earlier mock audit proves the pipeline, not
  production provider readiness.
- [ ] Confirm receipt of a real Azure alert notification and document restart
  recovery. Alert rules and the action group exist, but receiver delivery is
  not yet proven.
- [ ] Prepare and approve the production cutover window, owner, communications,
  DNS TTL, Stripe webhook move, custom-domain/TLS binding, smoke tests, and
  rollback decision point.
- [ ] During the authorized cutover, bind and validate `api.salti8.com`, replace
  the Render DNS target, move the Stripe webhook, run authenticated two-tenant
  browser and VirtuaPet checks, observe alerts and audit delivery, and retain
  the prior immutable image for rollback.
- [ ] Enable `VIRTUAPET_INTEGRATION_ENABLED`, `LAYER8_POLICY_ENABLED`, and
  `LAYER8_IDENTITY_LINKS_ENABLED` only after every preceding VirtuaPet gate has
  passed and the production configuration has been reviewed.

Production readiness is therefore **not complete**. The Azure candidate and
its core dependencies are healthy, and the Clerk organizations, memberships,
verifier, and Layer8 mappings are prepared. The blocking gates are real
authenticated tenant-isolation evidence, VirtuaPet UUID/key provisioning and
end-to-end denial tests, Stripe test-mode acceptance, provider-backed inference,
alert delivery, and the separately authorized DNS/TLS/webhook cutover.

## VirtuaPet boundary — 2026-09-16

Implemented a default-off, versioned VirtuaPet integration:

- `POST /v1/integrations/virtuapet/link-proof` verifies an existing Clerk organization and emits a five-minute ES256 challenge-bound proof without creating a tenant.
- `POST /v1/integrations/virtuapet/policy` authenticates a hashed, tenant-scoped API key requiring `virtuapet:policy`, verifies the identity proof and tenant mapping, rereads billing/entitlements, rate-limits and replay-protects through Redis, and emits a decision valid for at most 60 seconds.
- Only fixed nonclinical Pawsome3D preview and PawPath community actions are defined. Stripe plans and production entitlements were not changed.
- Errors and validation responses are non-cacheable and redact tokens and request bodies.

Evidence rechecked on 2026-09-16: 115 Python tests, Ruff, the TypeScript/static export, and the web dependency audit passed. The cross-repository stdio verifier also passed against the real VirtuaPet consumer without opening a network listener. GitHub CI run `35139652852` passed for commit `f743aa9`.

The same review found no managed signing key, explicit tenant mapping, or dedicated `virtuapet:policy` API key. VirtuaPet migration 005 has been applied successfully in Azure. Layer8 now has a dependency-ready Azure staging API and its authorized mock audit request completed through PostgreSQL, Service Bus, the audit worker, and Blob Storage. Operational gates remain: provision managed signing-key rotation, create explicit tenant mappings and distinct per-tenant scoped API keys, pass real two-tenant allowed/denied tests, configure alert notification routing, and complete Stripe test-mode and authenticated browser workflows. Provider activation and public DNS cutover have not occurred. Never substitute the Layer8 admin token for a VirtuaPet runtime credential.

See `docs/architecture/VIRTUAPET_INTEGRATION.md` for the contract and activation sequence.

## Azure migration — 2026-09-16

The replacement for suspended Render hosting created an isolated Azure staging foundation. At the 2026-09-16 checkpoint, revision `layer8-staging-api--0000002` used image `sha-3916de4`, with one minimum and three maximum replicas. CI runs `35156982413` and `35157645665` passed and published the implementation and final documentation images. Live probes returned 200 from `/healthz` and `/readyz`; readiness passed PostgreSQL, Redis, Blob Storage, and Service Bus. An unauthenticated admin request returned 401 and the disabled VirtuaPet policy route returned 503. Scheduled job `layer8-audit-worker` used image `sha-3916de4`; repeated executions succeeded. Authorized mock request `req_b35a610189964c378b6ffa89ea117626` and worker execution `layer8-audit-worker-0bavldi` produced the expected Blob; the temporary key was revoked, tenant disabled, and entitlement job deleted. A rollback drill to `sha-6049ea4` and restoration to `sha-3916de4` passed health and readiness. Keep Hostinger for the static SALTI8 build and leave `api.salti8.com` unchanged until the remaining real-tenant, alerting, webhook, custom-domain/TLS, and browser gates pass. See `docs/architecture/AZURE_STAGING_DEPLOYMENT.md` and `docs/runbooks/AZURE_PRE_CUTOVER.md`.

On 2026-09-17, Azure revision `layer8-staging-api--0000003` received managed P-256 VirtuaPet signing references, distinct link/policy audiences, and issuer configuration while remaining disabled. VirtuaPet received a separate managed identity/vault, public verification material only, and a separate link-encryption key; its revision `virtuapet-staging-api--0000002` remained disabled and ready. Exact trusted-origin CORS passed and an untrusted Layer8 origin was rejected. Action group `ag-layer8-staging` and restart/no-replica alerts are enabled. Remaining non-synthetic gates require two authenticated Clerk browser sessions, Stripe test credentials, alert-email receipt, and the Hostinger CNAME/TXT change that begins production cutover.

Clerk staging identity was corrected on 2026-09-17: VirtuaPet remains on Microsoft Entra, while Clerk is the SALTI8/Layer8 customer identity boundary. SALTI8 Development organizations `org_3JROrehaWBgw8CD22AWEcyHPWI4` and `org_3JROvg2ieivvKt1IrGexqN0tcMQ` map to active Layer8 tenants `salti8-staging-a` and `salti8-staging-b`. The Development JWT public verifier is stored in Layer8 Key Vault as `layer8-clerk-dev-jwt-public-key` and is attached to revision `layer8-staging-api--clerk5bfb`. Layer8 now accepts Clerk v2 `o.id` and legacy `org_id` only after signature verification and fails closed on malformed or conflicting claims. Both invitations have been accepted; two authenticated browser sessions and the correct-tenant/cross-tenant acceptance tests remain required before the Clerk gate is complete.
