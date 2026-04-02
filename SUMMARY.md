# Layer8 — Project & Commit Summary

## What is Layer8?

Layer8 is a **multi-tenant Enterprise AI Routing Proxy** built with FastAPI, PostgreSQL, Redis, MinIO/S3, and an SQS-compatible queue. It sits between client applications and AI providers (OpenAI, Gemini, etc.) and handles every cross-cutting concern that would otherwise be duplicated across teams:

| Concern | How Layer8 handles it |
|---|---|
| Authentication | Tenant-scoped API key validation on every request |
| Rate limiting | Redis-backed per-tenant limiter (in-memory fallback for tests) |
| Caching | Redis hot-cache + S3/MinIO spillover, keyed per-tenant |
| Plugin hooks | Before/after plugin pipeline around the provider call |
| Provider routing | Pluggable `ProviderAdapter` registry (mock, OpenAI, Gemini) |
| Audit logging | Async publish to SQS-compatible queue, consumed by a worker |
| Control plane | Admin REST API for tenant and API-key lifecycle management |
| Observability | `/healthz`, `/readyz`, structured boot logging, startup checks |

The fixed request path is: **auth → rate limit → before-plugins → cache-check → provider → cache-write → after-plugins → audit → response**.

Backend modes:
- `BACKEND_MODE=memory` — pure in-memory stores, for tests only
- `BACKEND_MODE=self_hosted` — PostgreSQL + Redis + MinIO + ElasticMQ

---

## Commit History

### Base branch (commits landed before this branch)

#### `a2cbe58` — Initial self-hosted AI routing proxy scaffold
The founding commit. Establishes the complete application skeleton:
- `app/` package with `api/`, `core/`, `db/`, `plugins/`, `providers/`, `schemas/`, `workers/` sub-packages
- FastAPI entry-point (`app/main.py`) and inference route (`POST /v1/proxy/infer`)
- 9-stage `InferencePipeline` in `app/core/pipeline.py`
- SQLAlchemy models + Alembic initial migration (tenants, API keys, audit records, cache entries)
- In-memory and self-hosted service implementations for auth, rate-limiting, cache, and audit
- `MockProvider` and `OpenAIChatProvider` adapter examples
- Docker Compose local stack (postgres, redis, minio, elasticmq)
- `scripts/bootstrap_local.py` seed script
- Makefile, `.env.example`, and README quick-start

#### `6aaedf8` — Fix local self-hosted bootstrap and queue emulator
Corrects the ElasticMQ URL used by the bootstrap script and queue emulator so that the local self-hosted stack starts cleanly without manual intervention. Updates `.env.example` and `docker-compose.yml` to match.

#### `33db13d` — Add audit queue worker process
Adds `app/workers/tasks.py` — a standalone worker process that polls the SQS-compatible audit queue and persists consumed records to the database. Adds the `AUDIT_WORKER_*` config fields and a `make worker` target.

#### `6215e2e` — Add GitHub Actions CI workflow
Introduces `.github/workflows/ci.yml`: install deps, run linter (`ruff`), run the test suite (`pytest`), on every push and pull request targeting `main`.

#### `4973740` — Add readiness endpoint
Adds `GET /readyz` via `app/services/readiness.py`. The endpoint probes the database, Redis, S3, and queue connections and returns `200 OK` only when all backing services are healthy. Adds companion tests (`tests/test_readiness.py`) and expands pipeline tests.

#### `6ea89d3` — Add startup checks and cleaner boot logging
Adds `app/services/startup.py` which runs a startup probe (controlled by `STARTUP_CHECKS_STRICT`) before accepting traffic. Structured JSON logging now emits a readable boot sequence. Tests in `tests/test_startup.py`.

#### `3f68614` — Add repo templates and deployment manifests
Adds production-ready packaging:
- `Dockerfile` and `.dockerignore`
- `deploy/docker-compose.prod.yml` (production compose file)
- Kubernetes base manifests: namespace, configmap, secret example, API deployment/service, worker deployment
- GitHub issue templates (bug report, feature request) and pull-request template

#### `b37fb2e` — Publish container image to GHCR
Extends the CI workflow to build the Docker image and publish it to GitHub Container Registry (`ghcr.io/robs46859-eng/layer8`) on every push to `main`, tagging with both `latest` and the short commit SHA.

#### `7cadb1a` — Add release workflow for tagged images *(tagged `v0.1.0`)*
Adds `.github/workflows/release.yml`: triggered on semantic version tags (e.g. `v0.1.0`), re-runs lint and tests, publishes versioned GHCR tags (`v0.1.0`, `0.1`, `0`, `latest`), and creates a GitHub Release with auto-generated notes. Also adds OCI metadata labels to all published images.

#### `cef393c` — Add staging and production deployment overlays
Restructures Kubernetes manifests under `deploy/kubernetes/base/` + Kustomize overlays:
- `overlays/staging/` — staging namespace, config, 1-replica counts, secret example
- `overlays/production/` — production namespace, config, 3-replica counts, secret example
- Adds `deploy/env/staging.env.example` and `deploy/env/production.env.example`

#### `15c638f` — Add staging and production deploy workflows
Adds two GitHub Actions deploy workflows:
- `deploy-staging.yml` — runs after a successful CI run on `main`; applies the staging Kustomize overlay and rolls out the new image
- `deploy-production.yml` — runs after a successful Release workflow; applies the production overlay
- Both support manual (`workflow_dispatch`) triggers and require `KUBE_CONFIG` and `K8S_SECRET_MANIFEST` GitHub Environment secrets

#### `cf71fd6` — Add product backlog document
Adds `BACKLOG.md` with 14 shaped backlog items across P0, P1, and P2 priorities, each with a goal and explicit acceptance criteria. Covers control-plane CRUD, provider hardening, admin auth/RBAC, observability, worker reliability, usage metering, and product UI.

#### `0c222d3` — Add ai-gateway-productization skill to repo
Adds the `.codex/skills/ai-gateway-productization/` skill, a reusable Codex context file that encodes the Deploy / Operate / Sell tracks for turning a working AI gateway scaffold into a shippable product. Includes `references/deployment-checklist.md` and `references/product-roadmap.md`.

#### `4267e8c` — Add admin tenant and API key control plane
Adds the full admin REST API under `/admin`:
- Tenant CRUD: `POST`, `GET`, `PATCH /admin/tenants`, `POST /admin/tenants/{id}/disable`
- API-key management: list, create, revoke, rotate per tenant
- `app/services/tenants.py` and `app/services/api_keys.py` service layer
- `app/api/admin.py` router, `app/api/dependencies.py` admin auth dependency (bearer token from `ADMIN_API_TOKEN`)
- `app/schemas/admin.py` request/response models
- Alembic migration `0002` adding lifecycle fields to `Tenant` and `ApiKey` models
- 172-line integration test suite in `tests/test_admin_control_plane.py`

#### `f004053` — Add Gemini provider and MamaNav AI gateway wiring
Adds `app/providers/gemini.py` — a `GeminiProvider` that uses Google's OpenAI-compatible endpoint (`generativelanguage.googleapis.com/v1beta/openai/`). Injects a MamaNav system prompt for the pregnancy/parenting AI use-case. Registers the provider in `InferencePipeline` and adds `GEMINI_API_KEY` to the settings.

#### `79b752a` — Add android-ai-gateway-wiring skill
Adds `.codex/skills/android-ai-gateway-wiring/SKILL.md` — a reusable Codex context file documenting the full end-to-end pattern for wiring a Jetpack Compose Android app to a Layer8 gateway: provider implementation on the server side, tenant and API key provisioning via the admin control plane, OkHttp client code, a coroutine ViewModel, Compose typing indicator animation, and a production checklist.

---

### This branch (`copilot/summarize-layer8-branch-commits`)

#### `f0227c3` — Initial plan
Copilot agent branch created to summarize Layer8 and the commit history above. This `SUMMARY.md` file is the primary deliverable.
