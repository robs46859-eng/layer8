# Azure pre-cutover runbook

Status: authorized cutover started on 2026-09-17. DNS ownership and the Azure CNAME are published; Azure managed-certificate issuance and public acceptance remain in progress.

## Release candidate

- Resource group: `rg-layer8-staging-westus3`
- Container App: `layer8-staging-api`
- Audit worker job: `layer8-audit-worker`
- Candidate revision: `layer8-staging-api--clerk5bfb`
- Active cutover image: `ghcr.io/robs46859-eng/layer8:sha-7c77566`
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
- [ ] Two real approved staging tenants pass authenticated isolation and cross-tenant denial tests. `salti8-staging-a` and `salti8-staging-b` map to separate SALTI8 Development organizations and each organization now has its separate invited member, but browser-session acceptance remains open.
- [ ] Clerk authenticated customer and billing flows pass against the candidate host. The Development issuer and Key Vault-backed public verifier are attached to revision `layer8-staging-api--clerk5bfb`; the remaining work requires an explicitly allowed Development web origin and one authenticated session per organization.
- [ ] Stripe test-mode signed webhook acceptance and unsigned rejection pass against the candidate host. No Stripe test secret, webhook secret, test Price IDs, or portal configuration was present in managed configuration.
- [x] Azure action group `ag-layer8-staging` and critical no-replica/high-severity restart alerts are enabled for the signed-in Azure operator email.
- [ ] Confirm delivery of an alert notification and pass restart recovery. Azure accepted the receiver and rules, but the CLI test-notification operation returned `no valid receivers`; do not claim delivered email until the recipient confirms it.
- [ ] The final DNS and webhook change plan has an operator, maintenance window, TTL, rollback owner, and communication plan.

Any unchecked gate blocks cutover. Do not replace a missing Clerk session, Stripe test secret, or provider credential with guessed data.

## Clerk staging identity

VirtuaPet keeps Microsoft Entra authentication. Clerk belongs to SALTI8/Layer8 customer access. Clerk dashboard workspace IDs are administrative containers and must not be used as customer organization IDs.

SALTI8 Development currently uses issuer `https://deep-emu-94.clerk.accounts.dev`. Its public verifier is stored in Key Vault as `layer8-clerk-dev-jwt-public-key`; the Clerk secret key is not required for JWT verification and must not be copied into this runbook. Layer8 maps these application organizations:

| Clerk organization | Layer8 tenant |
| --- | --- |
| `org_3JROrehaWBgw8CD22AWEcyHPWI4` (`SALTI8 Staging A`) | `salti8-staging-a` |
| `org_3JROvg2ieivvKt1IrGexqN0tcMQ` (`SALTI8 Staging B`) | `salti8-staging-b` |

Clerk v2 session tokens carry the active organization in `o.id`; legacy tokens use `org_id`. The API accepts both only after signature verification and rejects malformed or conflicting values. Final acceptance requires one real session for each organization, an allowed browser origin, and successful correct-tenant plus cross-tenant-denial checks against the candidate revision.

Current members are `rob@virtuapet.com` in SALTI8 Staging A and
`robs46859@gmail.com` in SALTI8 Staging B. The dashboard reports one member in
each organization. These memberships do not establish a VirtuaPet tenant map:
VirtuaPet remains on Microsoft Entra and still requires its two canonical
organization UUIDs before the integration can be provisioned.

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

The 2026-09-16 drill created revision `layer8-staging-api--rollback6049`, returned 200 from health and readiness, restored image `sha-3916de4`, and returned 200 from readiness again. That checkpoint used revision `layer8-staging-api--0000002`; the current candidate is recorded at the top of this runbook.

## DNS and monitoring preparation

- Live DNS still resolves `api.salti8.com` through `layer8.onrender.com`; this is expected before cutover.
- Azure has no `api.salti8.com` custom-domain binding yet. Bind and validate it only as part of the authorized cutover sequence.
- No metric or scheduled-query alert rules were found in `rg-layer8-staging-westus3`. An action group and notification recipient must be approved before operational alert acceptance can pass.

Update on 2026-09-17: the action group and two metric rules now exist. The remaining monitoring gate is actual notification receipt and restart-recovery evidence.

## Managed VirtuaPet trust material

- Layer8 Key Vault owns the P-256 PKCS8 signing private key, key ID `vp-layer8-stg-20260917-01`, distinct policy/link audiences, issuer, and public JWKS.
- The Layer8 Container App reads these through its user-assigned identity and remains `VIRTUAPET_INTEGRATION_ENABLED=false` because no approved tenant map or scoped tenant credentials exist.
- VirtuaPet has dedicated identity `id-virtuapet-staging` and vault `kv-virtuapet-stg-f7318c`. It stores only the pinned public JWKS/key ID and a separate random 32-byte link-encryption key.
- VirtuaPet revision `virtuapet-staging-api--0000002` has policy and identity-link endpoints configured but both enable flags remain false. Health and readiness returned 200.
- Never enable either service until two real tenant UUIDs, two Clerk organization IDs, explicit mappings, and two distinct API keys scoped exactly to `virtuapet:policy` have been provisioned and tested.

## Browser and CORS evidence

- Layer8 accepted the `https://salti8.com` preflight and returned its exact origin; an untrusted origin returned 400 without an allow-origin header.
- VirtuaPet accepted the `https://virtuapet.com` preflight and returned its exact origin.
- `salti8.com`, `virtuapet.com`, and `api.virtuapet.com/healthz` returned successful TLS verification.
- Authenticated browser acceptance remains open. The organizations, members,
  verifier, and Layer8 mappings now exist, but a Development Clerk frontend on
  an explicitly allowed origin and two retained authenticated sessions are
  still required for correct-tenant and cross-tenant tests.

## Custom-domain records required at cutover

Azure has not bound `api.salti8.com`. Hostinger DNS still points it to Render. During the separately approved cutover window, add ownership verification and replace the API CNAME using the values below, validate the managed certificate, then run authenticated smoke tests before removing rollback:

| Type | Host | Value |
| --- | --- | --- |
| TXT | `asuid.api` | `C933AFD753904BB50F319ACB99A46E6F5652305BFD297FF52D26BEB91EB7CE78` |
| CNAME | `api` | `layer8-staging-api.niceground-f0c7cfe6.westus3.azurecontainerapps.io` |

The CNAME replacement moves production traffic and therefore is the cutover itself, not harmless preparation.

## Cutover boundary

The later cutover is a separate explicitly authorized change. It includes the Hostinger DNS update for `api.salti8.com`, Azure custom-domain validation and certificate state, Stripe webhook destination movement, browser/CORS checks, authenticated smoke tests, monitoring, and rollback observation. Do not perform those steps merely because this runbook is green.
