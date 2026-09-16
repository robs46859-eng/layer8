# Azure pre-cutover runbook

Status: staging deployed; production traffic has not moved. This runbook stops immediately before DNS and Stripe webhook cutover.

## Release candidate

- Resource group: `rg-layer8-staging-westus3`
- Container App: `layer8-staging-api`
- Audit worker job: `layer8-audit-worker`
- Candidate image: `ghcr.io/robs46859-eng/layer8:sha-3916de4`
- Candidate FQDN: `layer8-staging-api.niceground-f0c7cfe6.westus3.azurecontainerapps.io`
- Public API DNS: `api.salti8.com` still targets Render and is not part of staging acceptance.

Never copy secret values into this file, shell history, CI output, or tickets. Key Vault references are the source of truth.

## Required green gates

- [x] Immutable image built by passing CI.
- [x] Dedicated PostgreSQL migrations completed through `20260728_0006`.
- [x] `/healthz` returns 200.
- [x] `/readyz` returns 200 with PostgreSQL, Redis, Blob Storage, and Service Bus all `ok`.
- [x] Missing admin authorization returns 401.
- [x] VirtuaPet policy integration remains disabled and returns 503.
- [x] Scheduled audit worker runs from the same immutable image.
- [x] Application rollback to `sha-6049ea4` and restoration to `sha-3916de4` both returned healthy and ready.
- [x] An authorized mock inference produced a database audit row, Service Bus delivery, and Blob object.
- [ ] Two real approved staging tenants pass isolation and cross-tenant denial tests.
- [ ] Clerk authenticated customer and billing flows pass against the candidate host.
- [ ] Stripe test-mode signed webhook acceptance and unsigned rejection pass against the candidate host.
- [ ] Alerts, notification routing, and restart recovery pass. No Azure alert rules were found on 2026-09-16.
- [ ] The final DNS and webhook change plan has an operator, maintenance window, TTL, rollback owner, and communication plan.

Any unchecked gate blocks cutover. Do not replace a missing real tenant, Clerk session, Stripe test secret, or provider credential with guessed data.

The audit acceptance request `req_b35a610189964c378b6ffa89ea117626` completed the ordered pipeline with the mock provider. Worker execution `layer8-audit-worker-0bavldi` succeeded and wrote `audit/cutover-audit-20260916/req_b35a610189964c378b6ffa89ea117626.json` as a 372-byte `application/json` Blob. The temporary API key was revoked, the temporary tenant was disabled, and the temporary entitlement job was deleted. The disabled test record and audit object remain as acceptance evidence.

## Smoke probes

```bash
export LAYER8_CANDIDATE_URL="https://layer8-staging-api.niceground-f0c7cfe6.westus3.azurecontainerapps.io"
curl --fail-with-body "$LAYER8_CANDIDATE_URL/healthz"
curl --fail-with-body "$LAYER8_CANDIDATE_URL/readyz"
curl -i "$LAYER8_CANDIDATE_URL/admin/tenants"
```

Expected results are 200, 200, and 401 respectively. A healthy probe is necessary but does not prove authenticated customer, billing, tenant isolation, or provider behavior.

## Rollback drill

1. Record the current image and revision.
2. Deploy the last known-good immutable image as a new revision; never rewrite an image tag.
3. Confirm `/healthz`, `/readyz`, and authorization denial behavior.
4. Redeploy the release candidate as a new revision and repeat the probes.
5. Record both revision names and timestamps in `HANDOFF.md`.

The database migration set must remain backward-compatible with both images used in the drill. Never roll the database backward during an application rollback.

The 2026-09-16 drill created revision `layer8-staging-api--rollback6049`, returned 200 from health and readiness, restored image `sha-3916de4`, and returned 200 from readiness again. The current release-candidate revision after scale configuration is `layer8-staging-api--0000002`, with one minimum and three maximum replicas.

## DNS and monitoring preparation

- Live DNS still resolves `api.salti8.com` through `layer8.onrender.com`; this is expected before cutover.
- Azure has no `api.salti8.com` custom-domain binding yet. Bind and validate it only as part of the authorized cutover sequence.
- No metric or scheduled-query alert rules were found in `rg-layer8-staging-westus3`. An action group and notification recipient must be approved before operational alert acceptance can pass.

## Cutover boundary

The later cutover is a separate explicitly authorized change. It includes the Hostinger DNS update for `api.salti8.com`, Azure custom-domain validation and certificate state, Stripe webhook destination movement, browser/CORS checks, authenticated smoke tests, monitoring, and rollback observation. Do not perform those steps merely because this runbook is green.
