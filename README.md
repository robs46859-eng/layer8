# SALTI8

SALTI8 is the product repository for **Layer8 Adaptive by SALTI8**, a
tenant-aware AI execution gateway with authentication, policy enforcement,
provider routing, usage controls, billing, and operational evidence.

The repository combines:

- the SALTI8 marketing and customer application in `apps/web`;
- the FastAPI gateway and billing API in `app`;
- PostgreSQL, Redis, S3-compatible archive, and queue integrations;
- deployment, migration, and launch runbooks in `docs/runbooks`.

## Feature summary

### Available in the codebase

- **Tenant-aware AI gateway:** authenticates scoped API keys, separates tenant data, enforces rate limits and idempotency, runs bounded plugins, selects a provider, and records usage and audit evidence.
- **Provider routing and resilience:** supports mock, OpenAI-compatible, and Gemini paths with policy-based selection, retries, fallback controls, response caching, and prompt logging disabled by default.
- **Customer identity and billing:** maps Clerk organizations to Layer8 tenants and provides server-owned Stripe Checkout, subscription, invoice, entitlement, and customer-portal flows. Stripe secrets and administrative authority never belong in browser code.
- **Administration and pilots:** exposes protected API-only operations for tenant, API-key, entitlement, plugin, and pilot management. Platform administration requires its own token and is not granted by a normal Clerk session.
- **Spatial-service boundary:** supports separately authorized internal spatial workloads without turning that internal path into a customer or platform-admin bypass.
- **VirtuaPet policy boundary:** includes default-off signed identity-link and short-lived policy-decision contracts. Activation requires explicit tenant mapping, dedicated `virtuapet:policy` credentials, managed signing keys, consent, and two-tenant validation.
- **Durable self-hosted operation:** uses PostgreSQL for records, Redis for cache/rate/replay state, and an asynchronous audit pipeline. Audit transport can use AWS-compatible S3/SQS or Azure Blob Storage/Service Bus.
- **Static customer website:** builds a verified Next.js static export for Hostinger, including authentication and billing UI, search metadata, sitemap, social assets, and export-integrity checks.
- **Operational controls:** includes Alembic migrations, health and dependency readiness probes, structured redacted logs, environment validation, CI tests, immutable GHCR images, deployment runbooks, and rollback gates.

### Current deployment status

- The SALTI8 static site remains on Hostinger and the public `api.salti8.com` DNS name still points to the suspended Render service.
- An isolated Azure staging API is live at `layer8-staging-api.niceground-f0c7cfe6.westus3.azurecontainerapps.io`. Revision `layer8-staging-api--clerk5bfb` serves 100% of staging traffic from immutable image `sha-5bfb6f7`; PostgreSQL, Redis, Blob Storage, and Service Bus readiness checks pass.
- The scheduled Azure audit worker is deployed from the same immutable image, and manual execution `layer8-audit-worker-stcpf04` succeeded.
- SALTI8 Development Clerk verification is configured through a Key Vault-backed public key. Staging A and B each have a separate user and map to separate active Layer8 tenants. Authenticated two-browser tenant-isolation acceptance remains open.
- Stripe, real AI-provider, and VirtuaPet production activation is intentionally incomplete. Passing readiness does not authorize DNS cutover, webhook movement, tenant import, or integration enablement.

### Production readiness checklist

- [x] CI, immutable image publication, Azure API deployment, dependency readiness,
  audit-worker deployment, and rollback drill.
- [x] Separate SALTI8 Development organizations, users, and active Layer8 tenant
  mappings; Clerk issuer and public verifier configured on the Azure candidate.
- [x] Trusted SALTI8 CORS preflight succeeds; an untrusted origin and invalid
  customer sessions fail closed.
- [ ] Host a Development Clerk web build on an explicitly allowed staging origin.
- [ ] Keep one authenticated session for each staging user and prove correct-
  tenant access plus cross-tenant denial, expiry, membership removal, and
  revocation.
- [ ] Provide the two real VirtuaPet organization UUIDs and map them to the two
  Layer8 tenants. Layer8 tenant IDs such as `salti8-staging-a` are not VirtuaPet
  UUIDs.
- [ ] Create two distinct server-side keys scoped only to `virtuapet:policy`,
  store them in VirtuaPet Key Vault, and validate link, consent, replay,
  cancellation, expiry, revocation, tenant mismatch, and Redis-failure paths.
- [ ] Configure Stripe test-mode secrets, Prices, portal, and webhook; prove
  signed acceptance, unsigned rejection, Checkout, entitlement, cancellation,
  and portal behavior.
- [ ] Prove real provider inference and tenant-isolated database, queue, worker,
  and Blob audit evidence for both tenants.
- [ ] Confirm an actual alert notification and restart recovery.
- [ ] Approve and execute the `api.salti8.com` custom-domain/TLS, DNS, and Stripe
  webhook cutover with owners, monitoring, authenticated smoke tests, and a
  timed rollback decision.
- [ ] Enable the default-off Layer8/VirtuaPet flags only after every integration
  gate passes.

The project is **staging-ready at the infrastructure and Clerk-configuration
layers, but not fully production-ready**. The outstanding items require real
authenticated sessions, production-adjacent external services, or a deliberate
traffic cutover; health checks and synthetic mock evidence do not satisfy them.

## VirtuaPet policy integration

Layer8 Adaptive now includes a **default-off** VirtuaPet boundary at
`/v1/integrations/virtuapet`. A verified Clerk organization session can mint a
five-minute, challenge-bound account proof. A dedicated tenant API key with the
`virtuapet:policy` scope can then request a short-lived signed policy decision.
The provider rereads the current tenant, API-key, billing, and entitlement state
for every decision. It does not use platform-admin or internal-spatial bypasses.

The integration remains inactive. Managed P-256 signing material, separate link
and policy audiences, Redis, and public verification material are present in the
isolated Azure staging environments, but the two canonical VirtuaPet organization
UUIDs, explicit UUID-to-Layer8 mappings, and dedicated per-tenant keys scoped
exactly to `virtuapet:policy` are still missing. Both Layer8 and VirtuaPet enable
flags remain false. The Azure services are dependency-ready, but the public
Render endpoint remains suspended; neither condition is VirtuaPet activation
evidence. No Stripe product, price, webhook, or customer entitlement is changed
by this code. See
`docs/architecture/VIRTUAPET_INTEGRATION.md`.

Layer8 now has an isolated Azure staging stack. The API runs in Azure Container Apps with dedicated PostgreSQL, Azure Managed Redis, Key Vault, Blob Storage, Service Bus, and managed identities; Hostinger continues to serve the static website. Render remains the public API target until Azure passes every gate in `docs/runbooks/AZURE_PRE_CUTOVER.md`. The source supports both AWS S3/SQS and Azure Blob/Service Bus audit backends; the Azure worker is deployed and has completed both scheduled and manual executions.

## Production architecture

| Surface | Address | Responsibility |
| --- | --- | --- |
| Web | `https://salti8.com` | Static marketing, authentication, and billing UI |
| API | `https://api.salti8.com` | Authenticated gateway, customer billing, and Stripe webhooks |
| Identity | Clerk | User sessions and customer organizations |
| Billing | Stripe | Checkout, subscriptions, invoices, and customer portal |

Hostinger serves a static Next.js export:

```bash
npm ci
npm run build
```

The deployable web artifact is `apps/web/out`. Hostinger does not run a
persistent Node.js process. Clerk authentication runs in the browser, while
FastAPI validates Clerk session tokens and owns billing authorization at
`https://api.salti8.com`.

The web application uses the public domain `https://salti8.com`. The API and
signed Stripe webhook are deployed separately at `https://api.salti8.com`.

Customer authentication uses Clerk Organizations. The signed organization in
the customer session maps to a Layer8 tenant; authenticated FastAPI customer
endpoints then create Stripe Checkout and customer-portal sessions without
exposing Stripe or Layer8 credentials to the browser. In the public production
environment, an individual can sign up, name a workspace, and receive that
isolated tenant mapping automatically before choosing a plan. See:

- `docs/architecture/DEPLOYED_BUILD_BLUEPRINT.md`
- `docs/architecture/ACCESS_AND_ENTITLEMENT_SPECIFICATION.md`
- `docs/runbooks/ENVIRONMENT_MANAGEMENT.md`
- `docs/runbooks/AUDIT_STORAGE_SETUP.md`
- `docs/runbooks/HOSTINGER_DEPLOYMENT.md`
- `docs/runbooks/SEO_AND_INDEXING.md`
- `docs/runbooks/SANDBOX_AND_FIRST_CUSTOMER.md`
- `docs/runbooks/STRIPE_LIVE_SETUP.md`

### Configuration

`env/production.env` is the single source of truth for every environment value.
`scripts/envctl.py` validates it against a manifest and pushes it to Render over
the API, so configuration is never typed into a dashboard:

```bash
cp env/production.env.example env/production.env   # fill in, gitignored
export RENDER_API_KEY=rnd_...
python3 scripts/envctl.py validate
python3 scripts/envctl.py diff
python3 scripts/envctl.py push
python3 scripts/envctl.py doctor
```

The manifest encodes rules that are otherwise invisible — variables that must be
present but empty, values whose blankness produces a misleading error, and a
hard refusal to route any secret to a `NEXT_PUBLIC_*` build target. See
`docs/runbooks/ENVIRONMENT_MANAGEMENT.md`.

### Public site and search

Public marketing content is data-driven from `apps/web/lib/seo-content.ts`.
Adding an entry to `seoPages` generates the static route, canonical tag, Open
Graph and Twitter metadata, `WebPage`/`BreadcrumbList`/`FAQPage` JSON-LD,
internal links, and the sitemap entry. Absolute URLs come from
`apps/web/lib/site.ts` — never hard-code the origin elsewhere.

`npm run build` runs `next build` and then `apps/web/scripts/verify-export.mjs`,
which fails the build if `robots.txt`, `sitemap.xml`, `manifest.webmanifest`,
`404.html`, `.htaccess`, the icon set, the social cards, or any required route
is missing from `out/`, or if the sitemap advertises a URL that was not
exported. `docs/runbooks/SEO_AND_INDEXING.md` is the authority for canonical
URL shape, indexing policy, and post-deploy verification.

Clerk organization administration and Layer8 platform administration are
separate. The deployed website currently exposes customer billing and
entitlements. Platform `/admin` endpoints remain API-only and require the
separate `ADMIN_API_TOKEN`; a Clerk administrator does not automatically gain
that access.

The request path is fixed:

1. API key authentication
2. Rate limiting
3. Before plugins
4. Cache check
5. Provider routing
6. Cache write
7. After plugins
8. Audit logging
9. Response return

## Included

- FastAPI edge API with a thin inference endpoint
- Explicit service modules for auth, rate limiting, plugins, cache, routing, policy, and audit
- SQLAlchemy models plus Alembic migrations for PostgreSQL system-of-record entities
- Redis-backed limiter and cache implementations with in-memory fallbacks for tests
- S3/MinIO cache spillover and SQS-compatible audit publishing
- Provider adapter interface plus `mock` and OpenAI examples
- Local self-hosted Docker Compose stack
- Production-oriented Docker image and deployment manifests
- Seed/bootstrap script for a local tenant and API key
- Tests for pipeline order, auth failure, and tenant-scoped caching

## Quick Start

```bash
git clone https://github.com/robs46859-eng/layer8.git
cd layer8
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
docker compose up -d
python scripts/bootstrap_local.py
uvicorn app.main:app --reload
```

Use the dev key from `.env` as:

```text
X-API-Key: ak_live_demo.change-me-now
```

POST to `http://localhost:8000/v1/proxy/infer` with:

```json
{
  "model": "gpt-4.1-mini",
  "messages": [
    {"role": "user", "content": "Say hello"}
  ]
}
```

## Self-Hosted Local Stack

`docker-compose.yml` starts:

- `postgres` for system-of-record data
- `redis` for rate limits and hot cache metadata
- `minio` for S3-compatible object storage
- `elasticmq` for SQS-compatible queueing

Run migrations and seed data:

```bash
source .venv/bin/activate
alembic upgrade head
python scripts/bootstrap_local.py
```

The bootstrap script creates:

- the local S3 bucket
- the local audit queue
- a demo tenant and API key in PostgreSQL

## Admin Control Plane

Administrative endpoints are exposed under `/admin` and require a bearer token from `ADMIN_API_TOKEN`.

Set the token in `.env`:

```text
ADMIN_API_TOKEN=change-admin-token
```

Example admin requests:

```bash
curl -X POST http://localhost:8000/admin/tenants \
  -H "Authorization: Bearer ${ADMIN_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"tenant_alpha","name":"Tenant Alpha","data_residency":"us"}'
```

```bash
curl -X POST http://localhost:8000/admin/tenants/tenant_alpha/api-keys \
  -H "Authorization: Bearer ${ADMIN_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"scopes":["inference:invoke"],"allowed_models":["gpt-4.1-mini"]}'
```

Current control-plane endpoints:

- `POST /admin/tenants`
- `GET /admin/tenants`
- `GET /admin/tenants/{tenant_id}`
- `PATCH /admin/tenants/{tenant_id}`
- `POST /admin/tenants/{tenant_id}/disable`
- `GET /admin/tenants/{tenant_id}/api-keys`
- `POST /admin/tenants/{tenant_id}/api-keys`
- `POST /admin/api-keys/{key_id}/revoke`
- `POST /admin/api-keys/{key_id}/rotate`

## Backend Modes

- `BACKEND_MODE=memory`: in-memory auth/cache/rate-limit stores, intended for tests only
- `BACKEND_MODE=self_hosted`: PostgreSQL + Redis + MinIO + SQS-backed services

## Production Follow-Ups

- Move AWS credentials and provider secrets into a real secret manager
- Keep the API on an always-on paid service before accepting production traffic
- Run a dedicated worker process for audit/archive queue consumption
- Add admin APIs for tenants, routing policies, and provider accounts
- Harden plugin isolation beyond in-process execution if untrusted code is allowed

## Deployment

For a containerized deployment path:

```bash
docker build -t layer8:latest .
docker compose -f deploy/docker-compose.prod.yml up -d
```

On every push to `main`, GitHub Actions also publishes a container image to GitHub Container Registry:

```text
ghcr.io/robs46859-eng/layer8:latest
ghcr.io/robs46859-eng/layer8:sha-<commit>
```

Pull it with:

```bash
docker pull ghcr.io/robs46859-eng/layer8:latest
```

For tagged releases, push a semantic version tag such as `v0.1.0`:

```bash
git tag v0.1.0
git push origin v0.1.0
```

That triggers the release workflow, which:

- reruns lint and tests
- publishes versioned GHCR tags such as `v0.1.0`, `0.1.0`, `0.1`, `0`, and `latest`
- creates a GitHub Release with generated notes

Each published image also carries OCI labels for title, description, vendor, license, revision, and source metadata.

Production API infrastructure is declared in `render.yaml`. Render runs the
FastAPI service, audit worker, PostgreSQL database, and Key Value service.
Secrets and live Stripe identifiers are configured in Render, never committed.
