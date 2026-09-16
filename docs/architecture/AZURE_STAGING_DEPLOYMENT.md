# Layer8 Azure staging deployment

Status: isolated staging infrastructure and first API revision deployed on 2026-09-16. Render remains the current public DNS target until Azure acceptance passes.

## Target boundary

Layer8 moves to a dedicated Azure staging resource group in West US 3 while the SALTI8 static web application remains on Hostinger. Layer8 and VirtuaPet remain separate services and databases even when they share an Azure region.

| Capability | Azure service | Rule |
| --- | --- | --- |
| API | Azure Container Apps | Immutable GHCR image; one staging revision before scale-out |
| Schema migration | Container Apps Job | Alembic runs separately before API promotion |
| System of record | Azure Database for PostgreSQL Flexible Server | Dedicated Layer8 server/database and least-privilege runtime role |
| Rate limit, replay, cache | Azure Managed Redis | TLS, separate staging instance, fail closed for policy requests |
| Secrets | Azure Key Vault | User-assigned managed identity; no secret values in Git or deployment output |
| Audit archive | Azure Blob Storage | Private container and managed-identity access |
| Audit queue | Azure Service Bus | Dedicated queue, dead-letter handling, managed-identity sender/receiver roles |
| Logs | Existing Log Analytics workspace | Structured, redacted application and platform logs |

## Migration sequence

1. Provision the isolated staging resource group, identity, Key Vault, PostgreSQL, Managed Redis, Storage, Service Bus, Container App, and migration job.
2. Keep `VIRTUAPET_INTEGRATION_ENABLED=false`; do not create tenant policy keys before real tenant mapping exists.
3. Run Alembic through the migration job, then deploy the exact tested image. The initial legacy image still runs its idempotent migration entrypoint; a later revision must switch to an explicit `uvicorn` command so application replicas never own schema migration.
4. Build and verify the Azure Blob/Service Bus audit adapters before enabling the audit worker.
5. Pass `/healthz`, `/readyz`, protected-route denial, admin denial, PostgreSQL, Redis, archive, queue, restart, revision rollback, and two-tenant isolation checks.
6. Import or recreate tenants only from authenticated source records. Never infer mappings from email, DNS, or caller input.
7. Configure Clerk, Stripe, provider credentials, signing keys, and dedicated `virtuapet:policy` credentials through Key Vault references.
8. Change `api.salti8.com` only after webhook, browser, authenticated tenant, observability, and rollback acceptance. Retain Render as rollback until the Azure release is proven.

## Initial staging limitations

- The suspended Render service cannot currently provide an authenticated database export or secret inventory.
- A fresh Azure staging database is not evidence that Render tenants, billing records, API keys, or audit history were migrated.
- The deployed `sha-3030a4f` container still uses AWS S3/SQS interfaces for audit readiness and processing. Azure-native Blob/Service Bus support is implemented in source but requires a new immutable image and live worker verification.
- Publishing an image or obtaining a Container Apps FQDN does not activate VirtuaPet integration or authorize production DNS cutover.

## Acceptance evidence

Record immutable image digest, migration execution, resource IDs, managed-identity role assignments, secret reference names, dependency readiness, HTTP probes, authenticated tenant tests, rollback result, and DNS/TLS evidence. Never record credential values.

## 2026-09-16 deployment evidence

- Resource group: `rg-layer8-staging-westus3`; user-assigned identity: `id-layer8-staging`.
- Dedicated PostgreSQL 16 server/database: `pg-layer8-stg-f7318c` / `layer8`; migration job execution `layer8-db-migrate-lwqj9xo` succeeded through revision `20260728_0006`.
- Managed Redis cluster/database: `redis-layer8-stg-f7318c`, encrypted port 10000; its access URL is stored only as Key Vault secret `layer8-redis-url`.
- Private audit storage: `stlayer8stgf7318c` container `audit`; Service Bus namespace/queue: `sb-layer8-stg-f7318c` / `layer8-audit`.
- Container App: `layer8-staging-api`; Azure staging FQDN `layer8-staging-api.niceground-f0c7cfe6.westus3.azurecontainerapps.io`.
- Current revision `layer8-staging-api--0000002` runs immutable image `sha-3916de4` with one minimum and three maximum replicas. `/healthz` and `/readyz` returned 200; PostgreSQL, Redis, Blob Storage, and Service Bus checks all passed.
- Unauthenticated `/admin/tenants` returned 401, and the intentionally disabled VirtuaPet policy endpoint returned 503.
- Scheduled job `layer8-audit-worker` uses the same image. Authorized mock request `req_b35a610189964c378b6ffa89ea117626` completed the full request pipeline; worker execution `layer8-audit-worker-0bavldi` wrote the expected tenant/request-scoped JSON Blob. The temporary API key was revoked, tenant disabled, and entitlement job deleted.
- A rollback drill to `sha-6049ea4` and restoration to `sha-3916de4` passed health and readiness. DNS still targets Render, no Azure custom domain is bound, and no alert rules were found; these remain explicit pre-cutover gates.
- Key Vault holds only named runtime references: `layer8-database-url`, `layer8-redis-url`, `layer8-admin-api-token`, and `layer8-ghcr-token`.
