# Production Gates and Phase 4 Operational Validation Specification

Document ID: `SPEC-PROD-PHASE4-001`  
Date: September 17, 2026  
Status: Authoritative Architectural Specification  
Target Systems: SALTI8 / Layer8 Adaptive (`api.salti8.com`) & VirtuaPet (`api.virtuapet.com`)  

---

## 1. Executive Summary & Context

This specification defines the remaining architectural and operational gates required to promote the Layer8 Adaptive ↔ VirtuaPet integration and the underlying cloud foundations into full production readiness.

While infrastructure deployment (Azure Container Apps, Key Vault, PostgreSQL, Redis, Service Bus, Blob Storage), DNS/custom domain bindings (`api.salti8.com`), and base cryptographic trust material are deployed and healthy, operational closeout requires concrete evidence across five strict gates:
1. **Signed Identity-Link Activation**: End-to-end cryptographic account binding between Microsoft Entra ID (VirtuaPet) and Clerk (Layer8/SALTI8).
2. **Signed-Policy Interoperability & Failure Testing**: Strict enforcement of `virtuapet.layer8.policy.v1`, multi-tenant isolation, and fail-closed denial behavior.
3. **Live Billing Lifecycle Verification**: End-to-end Stripe live lifecycle evidence (checkout, entitlement provisioning, portal updates, cancellation) beyond synthetic webhook checks.
4. **Alert Delivery & Operational Observability**: Receipt of live Azure alert notifications and verified container restart recovery.
5. **Phase 4 Operational Validation**: VirtuaPet Phase 4 closeout encompassing spatial-manifest signing, PostgreSQL forced RLS and transaction-bound identity, replica persistence, and non-destructive restore drills.

---

## 2. Gate 1 — Signed Identity-Link Activation Architecture

### 2.1 Identity Boundaries & Mappings
- **VirtuaPet Identity Boundary**: Microsoft Entra ID (OIDC Issuer: `https://login.microsoftonline.com/19f458a5-6f26-4cf3-be66-0dae08ac9a07/v2.0`, Audience: `21320b3e-6ca0-4467-a569-f3f31e9b85e1`).
- **Layer8 / SALTI8 Identity Boundary**: Clerk Development (`https://deep-emu-94.clerk.accounts.dev`).
- **Explicit Tenant Mapping**:
  - **Tenant A**: VirtuaPet Org UUID `62335dff-756b-47a7-ba94-95e240c3680d` ↔ Layer8 Tenant `salti8-staging-a` (Clerk Org: `org_3JROrehaWBgw8CD22AWEcyHPWI4`, User: `rob@virtuapet.com`).
  - **Tenant B**: VirtuaPet Org UUID `6d8bed91-b840-4884-9ecb-907b4cf0c65f` ↔ Layer8 Tenant `salti8-staging-b` (Clerk Org: `org_3JROvg2ieivvKt1IrGexqN0tcMQ`, User: `robs46859@gmail.com`).

### 2.2 Activation Lifecycle & Protocol Sequence
```
VirtuaPet Client                VirtuaPet API                  Layer8 API
     |                                |                            |
     | 1. POST .../links/challenges   |                            |
     |------------------------------->|                            |
     | 2. { challengeId, nonce }      |                            |
     |<-------------------------------|                            |
     |                                |                            |
     | 3. POST .../virtuapet/link-proof (with Clerk Bearer token)   |
     |------------------------------------------------------------>|
     | 4. { proofToken (ES256 JWT) }                               |
     |<------------------------------------------------------------|
     |                                |                            |
     | 5. POST .../links/complete (challengeId, proofToken)        |
     |------------------------------->|                            |
     |                                | [Encrypt with AES-256-GCM] |
     |                                | [Store in PostgreSQL RLS]  |
     | 6. HTTP 200 Link Established   |                            |
     |<-------------------------------|                            |
```

### 2.3 Cryptographic & Data Protection Controls
1. **Link Proof JWT Structure**:
   - Header: `alg: ES256`, `typ: vp-layer8-link+jwt`, `kid: vp-layer8-stg-20260917-01`.
   - Claims: `iss`, `aud`, `sub` (VirtuaPet user UUID), `tenantId` (VirtuaPet org UUID), `challengeId`, `nonce`, `protocol: virtuapet.layer8.link.v1`, `providerSubject` (Clerk user ID), `providerTenantId` (Layer8 tenant), `providerOrganizationId` (Clerk org ID), `iat`, `exp` (<= 300 seconds), `jti`.
2. **At-Rest Protection**:
   - Proof tokens are never stored in plaintext. Encrypted using AES-256-GCM with a random 96-bit IV and authenticated additional data (AAD) binding tenant ID, user ID, and link ID.
   - Encryption key (`INTEGRATION_LINK_ENCRYPTION_KEY_BASE64`) is stored strictly in Azure Key Vault and never shared with Layer8.
3. **Challenge Atomicity & Expiry**:
   - Challenge TTL is strictly 300 seconds.
   - Challenges are single-use and consumed atomically inside a PostgreSQL transaction using row locks.

---

## 3. Gate 2 — Signed-Policy Interoperability & Failure Matrix

### 3.1 Policy Evaluation Specification
- **Endpoint**: `POST /v1/integrations/virtuapet/policy` on `api.salti8.com`.
- **Authentication**: Tenant-scoped API key requiring `virtuapet:policy` scope in `Authorization: Bearer <key>`.
- **Payload**:
  ```json
  {
    "identityProof": "<AES-256-GCM Decrypted Proof Token>",
    "action": "spatial.preview.read",
    "resource": "pawsome3d:order:<uuid>",
    "purpose": "owner_visual_preview",
    "requiredEntitlements": ["spatial.preview"],
    "correlationId": "<uuid>"
  }
  ```
- **Response**: Signed decision token (ES256, max validity 60 seconds) indicating `outcome: "allow"` or `outcome: "deny"`.

### 3.2 Required Failure & Negative Test Matrix
Execution must explicitly prove each of the following rejection conditions prior to enabling production traffic:
1. **Cross-Tenant Access A → B**: User authenticated in Tenant A presenting Organization B context must receive HTTP 403 Forbidden.
2. **Cross-Tenant Access B → A**: User authenticated in Tenant B presenting Organization A context must receive HTTP 403 Forbidden.
3. **Mismatched Link Proof Signature**: Clerk User B attempting to sign Challenge issued for Tenant A must return HTTP 400/403 with `proof_mismatch`.
4. **Mismatched Link Proof Signature B**: Clerk User A attempting to sign Challenge issued for Tenant B must return HTTP 400/403 with `proof_mismatch`.
5. **Expired Challenge**: Completion attempted after 301 seconds must return HTTP 400 `challenge_expired`.
6. **Replayed Challenge**: Re-submitting a previously completed challenge must return HTTP 400 `challenge_already_consumed`.
7. **Replayed Proof Token**: Re-using a proof token across distinct challenges must be rejected.
8. **Revoked API Key**: Policy invocation using a disabled or revoked tenant policy key must return HTTP 401 Unauthorized.
9. **Consent Revocation**: Calling `DELETE /v1/integrations/layer8/links/:linkId` must immediately prevent downstream policy decisions.
10. **Redis Dependency Outage**: Simulating Redis unavailability must cause policy evaluation to fail closed (HTTP 503/500) rather than failing open.

---

## 4. Gate 3 — Live Billing Lifecycle Verification Architecture

### 4.1 Transition from Synthetic to Full Lifecycle
Synthetic webhook testing proves signature validation and handler routing. Production readiness requires proving the end-to-end customer subscription lifecycle against live Stripe endpoints without manual workarounds.

### 4.2 Approved Live Catalog & Webhook Matrix
- **Plan Catalog**:
  - `price_1TyIL16X8IBUtLKflisiPVqI`: SALTI8 Team ($99 / month)
  - `price_1TyILs6X8IBUtLKf5HDS6fVs`: SALTI8 Business ($299 / month)
- **Billing Portal Configuration**: `bpc_1TDTW96X8IBUtLKfZd4HKkRk`
- **Active Webhook**: `we_1TyGny6X8IBUtLKfRnuQQCpE` listening on `https://api.salti8.com/v1/billing/webhook` for 11 critical events:
  - `checkout.session.completed`
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `customer.subscription.paused`
  - `customer.subscription.resumed`
  - `invoice.paid`
  - `invoice.payment_failed`
  - `payment_intent.succeeded`
  - `payment_intent.payment_failed`
  - `customer.updated`

### 4.3 Controlled Execution Protocol (No Live Payment)
1. **Live Checkout Session Generation**:
   - Generate a valid checkout session via `POST /v1/billing/checkout` using live price IDs.
   - Verify that session creation associates the customer with the authenticated Layer8 tenant ID.
2. **Entitlement State Verification**:
   - Verify initial state: `status: unbilled`, entitlements: `[]`.
   - Rehearse event processing through signed synthetic fixtures in live mode to verify PostgreSQL entitlement assignment.
3. **Billing Portal Navigation**:
   - Create portal session via `POST /v1/billing/portal` and verify valid redirect URL generated with active portal configuration.
4. **Subscription Cancellation & Revocation**:
   - Trigger subscription cancellation event and verify tenant entitlement revocation, cache invalidation in Redis, and fail-closed denial on policy evaluation.

---

## 5. Gate 4 — Alert Delivery & Operational Observability

### 5.1 Azure Alert Infrastructure
- **Action Group**: `ag-layer8-staging` (Resource Group: `rg-layer8-staging-westus3`).
- **Active Rules**:
  1. `layer8-container-restart-alert`: Triggers upon container restart or crash-loop backoff.
  2. `layer8-zero-replica-alert`: Triggers if active healthy replica count drops below 1.
  3. `layer8-high-memory-alert`: Triggers if container memory exceeds 80% for > 5 minutes.

### 5.2 Live Delivery Verification Procedure
1. Execute test notification via Azure Monitor CLI / REST API for Action Group `ag-layer8-staging`.
2. Confirm receipt in destination operator mailbox without transmission errors.
3. Perform a controlled rolling restart (`az containerapp revision restart`) and verify that recovery occurs within 30 seconds while health probes pass.

---

## 6. Gate 5 — VirtuaPet Phase 4 Operational Validation

### 6.1 Spatial Asset Manifest Signing
- **Contract**: Version 2 spatial manifest specification (`HMAC-SHA256`).
- **Validation**:
  - Pinned HTTPS GLB asset URLs only; non-HTTPS or unverified origins strictly rejected.
  - Verification of asset SHA-256 digest against manifest metadata.
  - Validation of coordinate systems, units (meters), bounding boxes, laterality, and client semantic compatibility.

### 6.2 PostgreSQL Transaction-Bound Identity & Forced RLS
- **Schema Validation**: Verify that migration `005_integration_identity_links.sql` enforces RLS across all integration tables.
- **Transaction Scope**: Ensure every database query runs within a scoped transaction establishing:
  ```sql
  SET LOCAL app.tenant_id = '<tenant-uuid>';
  SET LOCAL app.user_id = '<user-uuid>';
  ```
- **Privilege Separation**:
  - `virtuapet_migrator`: DDL and migration execution only.
  - `virtuapet_app`: DML with forced RLS; `BYPASSRLS` strictly disabled.
  - `virtuapet_readonly`: Read-only reporting role.

### 6.3 Resilience & Disaster Recovery Drills
1. **Replica Replacement Persistence**:
   - Deploy new container revision and verify authenticated user sessions and active links persist across replica termination.
2. **Non-Destructive Point-in-Time Restore (PITR)**:
   - Validate Azure PostgreSQL flexible server backup configuration and execute a non-destructive restore drill into a temporary isolated staging database.

---

## 7. Operational Cutover Sequencing & Rollback Protocol

### 7.1 Execution Sequence
1. Step 1: Complete isolated Clerk sessions A & B.
2. Step 2: Acquire Entra ID tokens A & B.
3. Step 3: Enable `VIRTUAPET_INTEGRATION_ENABLED=true` on `layer8-staging-api`.
4. Step 4: Enable `LAYER8_IDENTITY_LINKS_ENABLED=true`, `LAYER8_POLICY_ENABLED=false` on `virtuapet-staging-api`.
5. Step 5: Execute and complete account links for Tenant A and Tenant B.
6. Step 6: Execute all 10 failure/denial test cases (Gate 2).
7. Step 7: Enable `LAYER8_POLICY_ENABLED=true`.
8. Step 8: Remove temporary localhost origin from CORS and Clerk authorized parties.
9. Step 9: Verify `api.salti8.com` custom domain, TLS certificate, and DNS resolution.

### 7.2 Emergency Rollback Trigger Conditions & Procedure
If any link completion fails, cross-tenant denial fails open, or readiness fails:
```bash
az containerapp update \
  --resource-group rg-layer8-staging-westus3 \
  --name layer8-staging-api \
  --revision-suffix safedown \
  --set-env-vars "VIRTUAPET_INTEGRATION_ENABLED=false"

az containerapp update \
  --resource-group rg-virtuapet-staging-eastus \
  --name virtuapet-staging-api \
  --revision-suffix safedown \
  --set-env-vars "LAYER8_POLICY_ENABLED=false" "LAYER8_IDENTITY_LINKS_ENABLED=false"
```
Do NOT roll back `STRIPE_LIVE_MODE` unless billing regression is explicitly detected.
