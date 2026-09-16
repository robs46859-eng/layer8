# Layer8 Adaptive Integration Handoff

## VirtuaPet boundary — 2026-09-16

Implemented a default-off, versioned VirtuaPet integration:

- `POST /v1/integrations/virtuapet/link-proof` verifies an existing Clerk organization and emits a five-minute ES256 challenge-bound proof without creating a tenant.
- `POST /v1/integrations/virtuapet/policy` authenticates a hashed, tenant-scoped API key requiring `virtuapet:policy`, verifies the identity proof and tenant mapping, rereads billing/entitlements, rate-limits and replay-protects through Redis, and emits a decision valid for at most 60 seconds.
- Only fixed nonclinical Pawsome3D preview and PawPath community actions are defined. Stripe plans and production entitlements were not changed.
- Errors and validation responses are non-cacheable and redact tokens and request bodies.

Local evidence: 115 Python tests passed and Ruff passed. A cross-repository stdio verifier exercises the real Layer8 routes and signatures against the real VirtuaPet consumer without opening a network listener. The web dependency audit reports zero vulnerabilities after upgrading Next.js, Sharp, and Nano ID.

Operational gates remain: managed signing-key creation and rotation, explicit tenant mappings, dedicated scoped API keys, Redis readiness, staging secret configuration, two-tenant allowed/denied tests, observability, rollback, and authenticated browser workflow validation. Provider activation and production deployment have not occurred.

See `docs/architecture/VIRTUAPET_INTEGRATION.md` for the contract and activation sequence.
