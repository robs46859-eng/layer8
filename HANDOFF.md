# Layer8 Adaptive Integration Handoff

## VirtuaPet boundary — 2026-09-16

Implemented a default-off, versioned VirtuaPet integration:

- `POST /v1/integrations/virtuapet/link-proof` verifies an existing Clerk organization and emits a five-minute ES256 challenge-bound proof without creating a tenant.
- `POST /v1/integrations/virtuapet/policy` authenticates a hashed, tenant-scoped API key requiring `virtuapet:policy`, verifies the identity proof and tenant mapping, rereads billing/entitlements, rate-limits and replay-protects through Redis, and emits a decision valid for at most 60 seconds.
- Only fixed nonclinical Pawsome3D preview and PawPath community actions are defined. Stripe plans and production entitlements were not changed.
- Errors and validation responses are non-cacheable and redact tokens and request bodies.

Evidence rechecked on 2026-09-16: 115 Python tests, Ruff, the TypeScript/static export, and the web dependency audit passed. The cross-repository stdio verifier also passed against the real VirtuaPet consumer without opening a network listener. GitHub CI run `35139652852` passed for commit `f743aa9`.

The same review found no managed signing key, explicit tenant mapping, or dedicated `virtuapet:policy` API key. VirtuaPet migration 005 has been applied successfully in Azure. Layer8 now has a dependency-ready Azure staging API, but operational gates remain: provision managed signing-key rotation, create explicit tenant mappings and distinct per-tenant scoped API keys, pass two-tenant allowed/denied tests, verify audit message-to-blob processing with a real authorized request, validate observability and rollback, and complete the authenticated browser workflow. Provider activation and public DNS cutover have not occurred. Never substitute the Layer8 admin token for a VirtuaPet runtime credential.

See `docs/architecture/VIRTUAPET_INTEGRATION.md` for the contract and activation sequence.

## Azure migration — 2026-09-16

The replacement for suspended Render hosting now has an isolated Azure staging foundation and API revision `layer8-staging-api--miclient` from image `sha-6049ea4`. CI run `35156982413` passed and published the image. Live probes returned 200 from `/healthz` and `/readyz`; readiness passed PostgreSQL, Redis, Blob Storage, and Service Bus. An unauthenticated admin request returned 401 and the disabled VirtuaPet policy route returned 503. Scheduled job `layer8-audit-worker` uses the same image, and manual execution `layer8-audit-worker-34g4od0` succeeded. Keep Hostinger for the static SALTI8 build and leave `api.salti8.com` unchanged until the remaining authenticated tenant, audit message-to-blob, observability, rollback, webhook, and browser gates pass. See `docs/architecture/AZURE_STAGING_DEPLOYMENT.md`.
