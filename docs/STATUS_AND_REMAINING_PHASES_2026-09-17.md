# SALTI8 / Layer8 production status and remaining phases

Status captured: 2026-09-17 during the authorized Azure cutover.

## Current verified state

- The Azure Container App runs immutable image
  `ghcr.io/robs46859-eng/layer8:sha-7c77566`. The image contains the Stripe
  SDK 15 compatibility fix, and GitHub Actions run `35230299072` passed.
- PostgreSQL, Redis, Blob Storage, and Service Bus pass `/readyz`. The audit
  worker has completed the documented queue-to-Blob acceptance path.
- Stripe live mode is configured through Key Vault references. Team uses
  `price_1TyIL16X8IBUtLKflisiPVqI`, Business uses
  `price_1TyILs6X8IBUtLKf5HDS6fVs`, and portal configuration
  `bpc_1TDTW96X8IBUtLKfZd4HKkRk` is active. Webhook destination
  `we_1TyGny6X8IBUtLKfRnuQQCpE` subscribes to the required 11 events.
- A fresh signed synthetic live-mode event returned HTTP 200 from the Azure
  candidate. An unsigned event returned HTTP 400. This verifies signature
  handling; it does not replace a real Checkout, renewal, cancellation, or
  portal lifecycle.
- SALTI8 Development Clerk organizations map to separate Layer8 tenants:

  | Clerk organization | Layer8 tenant | Staging user |
  | --- | --- | --- |
  | `org_3JROrehaWBgw8CD22AWEcyHPWI4` | `salti8-staging-a` | `rob@virtuapet.com` |
  | `org_3JROvg2ieivvKt1IrGexqN0tcMQ` | `salti8-staging-b` | `robs46859@gmail.com` |

- Clerk verification uses the Development issuer and a Key Vault-backed public
  verifier. Clerk remains the SALTI8 identity boundary; VirtuaPet remains on
  Microsoft Entra.
- The authorized DNS cutover replaced the suspended Render CNAME with the
  Azure Container Apps hostname and added Azure ownership verification. Azure
  custom-domain and managed-certificate issuance must be verified before this
  item is marked complete.

## Activation checklist

- [x] 1. Publish and deploy the immutable API candidate with passing CI.
- [x] 2. Configure separate Clerk organizations, users, tenant mappings, issuer,
  verifier, and exact authorized origins.
- [x] 3. Provision separate VirtuaPet organization mappings and tenant-scoped
  `virtuapet:policy` credentials in server-side Key Vault.
- [x] 4. Attach Stripe live secrets, live Price IDs, portal configuration, and
  the 11-event webhook destination; verify signed acceptance and unsigned
  rejection.
- [x] 5. Add Azure DNS ownership verification and move `api.salti8.com` from
  suspended Render to the Azure Container Apps hostname.
- [ ] 6. Confirm the Azure managed certificate is issued, public health and
  readiness pass through `https://api.salti8.com`, exact CORS passes, and the
  signed Stripe probe succeeds through the public hostname.
- [ ] 7. Complete two simultaneous authenticated Clerk sessions, prove each
  user can access only the mapped tenant, complete two Entra-backed VirtuaPet
  identity links, prove correct-tenant allow and cross-tenant denial, then
  enable the default-off integration flags.

## Remaining build-out phases

### Phase A — cutover closure

- Confirm managed TLS, public DNS from multiple resolvers, `/healthz`, `/readyz`,
  anonymous authorization denial, exact-origin CORS, and signed webhook
  delivery through the public hostname.
- Change `PUBLIC_API_URL` to `https://api.salti8.com`, rebuild the Hostinger
  static export for the public API URL, deploy it, and remove the temporary
  localhost origin after browser acceptance.
- Keep the prior immutable image and the old DNS target recorded for rollback
  until the observation window closes.

### Phase B — authenticated tenant and billing acceptance

- Retain one authenticated browser session per Clerk organization and record
  own-tenant success plus both cross-tenant denials.
- Exercise real Stripe live Checkout only with an approved transaction plan;
  then verify webhook-created entitlement, portal access, cancellation, and
  entitlement removal. Synthetic webhook evidence alone is insufficient.
- Verify session expiry, organization membership removal, API-key revocation,
  webhook replay, and billing cancellation fail closed.

### Phase C — VirtuaPet activation

- Enable `VIRTUAPET_INTEGRATION_ENABLED` only for the link rehearsal, while
  keeping policy enforcement disabled.
- Complete separate Entra-backed links for VirtuaPet Staging A and B, then test
  subject, tenant, challenge, expiry, consent-revocation, replay, and outage
  denials.
- Enable `LAYER8_IDENTITY_LINKS_ENABLED`, followed by
  `LAYER8_POLICY_ENABLED`, only after the corresponding acceptance evidence is
  captured for both tenants.

### Phase D — production operations

- Prove provider-backed inference and tenant-isolated database, queue, worker,
  and Blob audit evidence for each tenant.
- Confirm delivery of a real Azure alert and document restart recovery.
- Add a recurring restore drill, signing-key rotation exercise, Stripe
  reconciliation, and incident/rollback ownership.

Production readiness is not complete until the unchecked items above have
fresh evidence. The service is cutover-capable and billing configuration is
live, but authenticated tenant isolation, real billing lifecycle, VirtuaPet
link/policy activation, provider inference, and alert delivery remain separate
acceptance gates.
