# Enterprise AI Routing Proxy

FastAPI scaffold for a tenant-aware AI routing proxy with both a memory-backed dev mode and a self-hosted mode using PostgreSQL, Redis, MinIO/S3, and SQS-compatible queues.

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
- Seed/bootstrap script for a local tenant and API key
- Tests for pipeline order, auth failure, and tenant-scoped caching

## Quick Start

```bash
cd /Users/robert/layer8
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
- `localstack` for SQS-compatible queueing

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

## Backend Modes

- `BACKEND_MODE=memory`: in-memory auth/cache/rate-limit stores, intended for tests only
- `BACKEND_MODE=self_hosted`: PostgreSQL + Redis + MinIO + SQS-backed services

## Production Follow-Ups

- Move AWS credentials and provider secrets into a real secret manager
- Put the API behind TLS and a reverse proxy
- Run a dedicated worker process for audit/archive queue consumption
- Add admin APIs for tenants, routing policies, and provider accounts
- Harden plugin isolation beyond in-process execution if untrusted code is allowed
