# SALTI8

SALTI8 is the product repository for **Layer8 Adaptive by SALTI8**, a
tenant-aware AI execution gateway with authentication, policy enforcement,
provider routing, usage controls, billing, and operational evidence.

The repository combines:

- the SALTI8 marketing and customer application in `apps/web`;
- the FastAPI gateway and billing API in `app`;
- PostgreSQL, Redis, S3-compatible archive, and queue integrations;
- deployment, migration, and launch runbooks in `docs/runbooks`.

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
