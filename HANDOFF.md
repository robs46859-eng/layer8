# Layer8 Adaptive Integration Handoff

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

The replacement for suspended Render hosting now has an isolated Azure staging foundation. The current live release candidate is revision `layer8-staging-api--0000002`, image `sha-3916de4`, with one minimum and three maximum replicas. CI runs `35156982413` and `35157645665` passed and published the implementation and final documentation images. Live probes returned 200 from `/healthz` and `/readyz`; readiness passed PostgreSQL, Redis, Blob Storage, and Service Bus. An unauthenticated admin request returned 401 and the disabled VirtuaPet policy route returned 503. Scheduled job `layer8-audit-worker` uses image `sha-3916de4`; repeated executions succeeded. Authorized mock request `req_b35a610189964c378b6ffa89ea117626` and worker execution `layer8-audit-worker-0bavldi` produced the expected Blob; the temporary key was revoked, tenant disabled, and entitlement job deleted. A rollback drill to `sha-6049ea4` and restoration to `sha-3916de4` passed health and readiness. Keep Hostinger for the static SALTI8 build and leave `api.salti8.com` unchanged until the remaining real-tenant, alerting, webhook, custom-domain/TLS, and browser gates pass. See `docs/architecture/AZURE_STAGING_DEPLOYMENT.md` and `docs/runbooks/AZURE_PRE_CUTOVER.md`.

On 2026-09-17, Azure revision `layer8-staging-api--0000003` received managed P-256 VirtuaPet signing references, distinct link/policy audiences, and issuer configuration while remaining disabled. VirtuaPet received a separate managed identity/vault, public verification material only, and a separate link-encryption key; its revision `virtuapet-staging-api--0000002` remained disabled and ready. Exact trusted-origin CORS passed and an untrusted Layer8 origin was rejected. Action group `ag-layer8-staging` and restart/no-replica alerts are enabled. Remaining non-synthetic gates require two actual Clerk organizations and sessions, Stripe test credentials, alert-email receipt, and the Hostinger CNAME/TXT change that begins production cutover.
