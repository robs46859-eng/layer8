# Layer8 Adaptive Integration Handoff

## VirtuaPet boundary — 2026-09-16

Implemented a default-off, versioned VirtuaPet integration:

- `POST /v1/integrations/virtuapet/link-proof` verifies an existing Clerk organization and emits a five-minute ES256 challenge-bound proof without creating a tenant.
- `POST /v1/integrations/virtuapet/policy` authenticates a hashed, tenant-scoped API key requiring `virtuapet:policy`, verifies the identity proof and tenant mapping, rereads billing/entitlements, rate-limits and replay-protects through Redis, and emits a decision valid for at most 60 seconds.
- Only fixed nonclinical Pawsome3D preview and PawPath community actions are defined. Stripe plans and production entitlements were not changed.
- Errors and validation responses are non-cacheable and redact tokens and request bodies.

Evidence rechecked on 2026-09-16: 115 Python tests, Ruff, the TypeScript/static export, and the web dependency audit passed. The cross-repository stdio verifier also passed against the real VirtuaPet consumer without opening a network listener. GitHub CI run `35139652852` passed for commit `f743aa9`.

The same review found no local `env/production.env` or Render API credential and no evidence that a managed signing key, explicit tenant mapping, or dedicated `virtuapet:policy` API key had been provisioned. Fresh probes to `https://api.salti8.com/healthz` and `/readyz` returned 503 Service Suspended. VirtuaPet migration 005 has since been applied successfully in Azure, but Layer8 recovery is now the first activation blocker. Operational gates therefore remain: restore the existing Render API, regain its operator-controlled configuration path, confirm Redis readiness, provision managed signing-key rotation, create explicit tenant mappings and distinct per-tenant scoped API keys, configure staging secrets, and pass two-tenant allowed/denied tests, observability, rollback, and authenticated browser workflow validation. Provider activation and production deployment have not occurred. Never substitute the Layer8 admin token for a VirtuaPet runtime credential.

See `docs/architecture/VIRTUAPET_INTEGRATION.md` for the contract and activation sequence.

## Azure migration — 2026-09-16

The replacement for suspended Render hosting now has an isolated Azure staging foundation and first API revision. Keep Hostinger for the static SALTI8 web build and leave `api.salti8.com` unchanged until Azure acceptance. Dedicated PostgreSQL migrations succeeded, `/healthz` returned 200, Managed Redis and the private audit resources exist, and Azure Blob/Service Bus support is implemented in source. The new source image, worker path, `/readyz`, denial checks, rollback, and authenticated tenant tests still must pass before DNS or Stripe webhooks move. See `docs/architecture/AZURE_STAGING_DEPLOYMENT.md` for immutable resource and probe evidence.
