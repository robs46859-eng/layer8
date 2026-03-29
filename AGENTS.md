# AGENTS.md

## Cursor Cloud specific instructions

### Product overview

Enterprise AI Routing Proxy ("Layer8") — a multi-tenant FastAPI gateway that authenticates, rate-limits, caches, routes, and audits AI inference requests. See `README.md` for full architecture.

### Infrastructure services

The local dev stack (`docker compose up -d`) provides four services:

| Service | Port | Purpose |
|---|---|---|
| PostgreSQL 16 | 5432 | System-of-record (tenants, keys, audit rows) |
| Redis 7 | 6379 | Hot cache + sliding-window rate limiter |
| MinIO | 9000/9001 | S3-compatible object store (cache spillover, audit blobs) |
| ElasticMQ | 9324 | SQS-compatible queue (async audit archival) |

PostgreSQL and Redis are **required**; MinIO and ElasticMQ are optional (`STARTUP_CHECKS_STRICT=false` is the default).

### Running the application

```bash
# Start infrastructure
docker compose up -d

# Run migrations + seed data (idempotent)
.venv/bin/python scripts/bootstrap_local.py

# Start dev server with hot-reload
.venv/bin/uvicorn app.main:app --reload
```

The dev API key is `ak_live_demo.change-me-now` (configured via `DEV_API_KEY_PREFIX` / `DEV_API_KEY_SECRET` in `.env`).

### Key commands

| Action | Command |
|---|---|
| Lint | `.venv/bin/ruff check .` |
| Tests | `.venv/bin/pytest tests` |
| Compile check | `.venv/bin/python -m compileall app scripts tests` |
| Dev server | `.venv/bin/uvicorn app.main:app --reload` |
| Migrations | `.venv/bin/python -m alembic upgrade head` |
| Bootstrap | `.venv/bin/python scripts/bootstrap_local.py` |

### Gotchas

- Tests run with `BACKEND_MODE=memory` (in-memory stores), so they do **not** require Docker services. Only the dev server in `self_hosted` mode needs the Compose stack.
- The `bootstrap_local.py` script is idempotent — it runs Alembic migrations, creates the S3 bucket, creates the SQS queue, and seeds the demo tenant/API key.
- There is a pre-existing lint warning: `F401` unused import of `sqlalchemy.Text` in `app/db/models.py`.
- The `.env` file is loaded by `pydantic-settings` from the project root; `cp .env.example .env` is required before running the server.
- Docker in the Cloud Agent VM requires `fuse-overlayfs` storage driver and `iptables-legacy` — these are one-time setup steps, not needed in the update script.
