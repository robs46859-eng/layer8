# Layer8 Issue Backlog

## P0

### Control plane: tenant CRUD API
Labels: `priority:P0`, `area:control-plane`, `type:feature`

#### Goal
Add admin APIs to create, list, update, and disable tenants without manual database edits.

#### Acceptance Criteria
- Create tenant endpoint exists
- List tenant endpoint exists
- Update tenant endpoint exists
- Disable tenant endpoint exists
- Tenant state is persisted in Postgres
- Validation errors are explicit and consistent
- Tests cover happy path and auth failure cases

#### Notes
This is foundational for making the proxy operable as a product rather than a scaffold.

---

### Control plane: API key create/revoke/rotate API
Labels: `priority:P0`, `area:control-plane`, `type:feature`

#### Goal
Add admin APIs to manage tenant API keys safely.

#### Acceptance Criteria
- Create API key endpoint exists
- Revoke API key endpoint exists
- Rotate API key endpoint exists
- Only hashed key material is stored at rest
- Revoked keys fail closed
- Rotated keys preserve audit history
- Tests cover revoked and rotated key behavior

#### Notes
Key lifecycle management is required before external users or tenants can be onboarded.

---

### Control plane: provider config CRUD API
Labels: `priority:P0`, `area:control-plane`, `type:feature`

#### Goal
Allow operators to manage provider configuration through APIs instead of code or manual DB edits.

#### Acceptance Criteria
- Create provider config endpoint exists
- Update provider config endpoint exists
- List provider config endpoint exists
- Credentials are not returned in plaintext on reads
- Per-tenant enablement is supported
- Validation rejects invalid provider configs
- Tests cover config creation and invalid input cases

#### Notes
This is required before supporting multiple real providers cleanly.

---

### Routing: tenant routing policy CRUD API
Labels: `priority:P0`, `area:routing`, `type:feature`

#### Goal
Allow per-tenant routing behavior to be managed through the control plane.

#### Acceptance Criteria
- Admin can define default provider and model per tenant
- Policy supports allowlist and denylist style constraints
- Invalid policy combinations are rejected
- Runtime policy changes are applied without app restart
- Tests cover policy read and enforcement behavior

#### Notes
This is the control layer that makes the proxy valuable.

---

### Provider: harden OpenAI adapter
Labels: `priority:P0`, `area:provider`, `type:feature`

#### Goal
Move the OpenAI provider path from example-level support to production-capable support.

#### Acceptance Criteria
- Real request path works with configured OpenAI credentials
- Upstream errors are translated into clear proxy responses
- Timeout behavior is configurable
- Usage metadata is normalized into the proxy schema
- Tests cover success, timeout, and upstream error cases

#### Notes
This should be the first real provider integration to harden.

---

### Security: admin auth and RBAC
Labels: `priority:P0`, `area:security`, `type:feature`

#### Goal
Protect control-plane endpoints with admin authentication and role-based authorization.

#### Acceptance Criteria
- Control-plane endpoints require admin authentication
- Roles support at least read-only and admin
- Unauthorized and forbidden responses are distinct
- Tests cover role enforcement and denial paths
- Auth model is documented

#### Notes
Without this, the control plane is not safe to expose.

---

### Observability: Prometheus metrics
Labels: `priority:P0`, `area:observability`, `type:infra`

#### Goal
Expose operational metrics suitable for dashboards and alerts.

#### Acceptance Criteria
- Metrics endpoint exists
- Request count and latency metrics exist
- Cache hit/miss metrics exist
- Provider error metrics exist
- Worker failure metrics exist
- Metrics do not expose secrets or prompt bodies
- Docs explain how to scrape and interpret the metrics

#### Notes
This is required for production support and SLOs.

---

### Worker: DLQ and retry support for audit processing
Labels: `priority:P0`, `area:worker`, `type:infra`

#### Goal
Make audit processing resilient under failures.

#### Acceptance Criteria
- Failed audit messages are retried with backoff
- Poison messages can be routed to a dead-letter path
- Replay tooling or replay procedure exists
- Worker processing remains idempotent
- Tests cover retry and duplicate-processing cases

#### Notes
Audit durability is one of the product's core promises.

---

## P1

### Usage: persist request and token metering by tenant/provider/model
Labels: `priority:P1`, `area:control-plane`, `type:feature`

#### Goal
Track request and token usage in a way that supports reporting and chargeback.

#### Acceptance Criteria
- Usage rows are stored in Postgres
- Aggregation by tenant, provider, model, and day is possible
- Cached and non-cached requests are distinguishable
- Tests cover aggregation correctness
- Schema is documented

#### Notes
This enables cost reporting and later billing features.

---

### Security: secret manager integration
Labels: `priority:P1`, `area:security`, `type:infra`

#### Goal
Resolve provider and infrastructure secrets from a real secret backend.

#### Acceptance Criteria
- One real secret manager is supported
- App can resolve secrets without relying only on plain env values
- Failure mode is explicit and observable
- Staging and production setup is documented
- Tests cover secret resolution failure behavior

#### Notes
GitHub/Kubernetes secrets are delivery mechanisms, not the real source of truth.

---

### Routing: provider failover support
Labels: `priority:P1`, `area:routing`, `type:feature`

#### Goal
Allow configured fallback providers when the primary provider fails.

#### Acceptance Criteria
- Failover can be enabled by routing policy
- Configured upstream failures trigger fallback
- Audit trail records the failover decision
- Tests cover primary failure and fallback success
- Metrics capture fallback frequency

#### Notes
This is important for real production reliability.

---

### Policy engine: model allowlists and per-tenant limits
Labels: `priority:P1`, `area:routing`, `type:feature`

#### Goal
Add enforceable policy controls at request time.

#### Acceptance Criteria
- Tenant policies can restrict allowed models
- Violations fail closed
- Policy can differ by environment
- Tests cover enforcement in the request pipeline
- Policy behavior is operator-visible

#### Notes
This is a core governance feature.

---

### Observability: provider latency and error dashboards
Labels: `priority:P1`, `area:observability`, `type:infra`

#### Goal
Provide operator-facing visibility into health and performance.

#### Acceptance Criteria
- Dashboard definitions exist
- Provider latency is visible
- Provider error rates are visible
- Queue backlog is visible
- Worker failure signals are visible
- Documentation explains the core operational views

#### Notes
This should build directly on the Prometheus metrics work.

---

### Deployment: staging smoke test after deploy
Labels: `priority:P1`, `area:deploy`, `type:infra`

#### Goal
Automatically validate a staging deployment after rollout.

#### Acceptance Criteria
- Workflow verifies `/healthz`
- Workflow verifies `/readyz`
- Workflow performs at least one authenticated inference request
- Deployment fails if smoke test fails
- Logs are visible in GitHub Actions output

#### Notes
This closes the loop between image publishing and actual operability.

---

## P2

### Admin UI: tenant and API key management screens
Labels: `priority:P2`, `area:product`, `type:feature`

#### Goal
Provide a basic operator UI for the most common control-plane tasks.

#### Acceptance Criteria
- Admin can create tenants
- Admin can issue keys
- Admin can revoke keys
- Sensitive values are not re-shown after creation
- Basic audit events are visible
- UI uses existing admin auth model

#### Notes
This can start minimal. It does not need to be polished first.

---

### Admin UI: usage dashboard
Labels: `priority:P2`, `area:product`, `type:feature`

#### Goal
Expose usage and traffic data through a simple UI.

#### Acceptance Criteria
- Requests, tokens, and cache hit rate are shown
- Provider distribution is shown
- Filtering by tenant and date range is supported
- Empty and loading states are handled
- Export path exists or is defined

#### Notes
This helps tell the product story during demos.

---

### Compliance: redaction plugin framework
Labels: `priority:P2`, `area:security`, `type:feature`

#### Goal
Support request redaction before prompts are sent upstream.

#### Acceptance Criteria
- Before-plugin hook can redact configured fields
- Redaction behavior is explicit and testable
- Audit behavior for original vs redacted payload is documented
- Tests verify redaction occurs before provider call

#### Notes
This is a strong wedge for regulated use cases.

---

### Docs: architecture and security overview
Labels: `priority:P2`, `area:product`, `type:docs`

#### Goal
Create operator- and buyer-friendly documentation for the system.

#### Acceptance Criteria
- Architecture overview exists
- Trust boundaries are described
- Secret handling is documented
- Audit behavior is documented
- Deployment assumptions are explicit

#### Notes
This is important for pilots and procurement conversations.

---

### Productization: example integrations
Labels: `priority:P2`, `area:product`, `type:docs`

#### Goal
Make it easy for teams to adopt `layer8` from real application code.

#### Acceptance Criteria
- At least one Python example exists
- At least one Node example exists
- Examples show auth, request format, and error handling
- Local quickstart works against the proxy stack
- README links to the examples

#### Notes
Examples reduce adoption friction and improve demos.
