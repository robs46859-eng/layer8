---
name: ai-gateway-productization
description: Turn an AI routing proxy or gateway into a deployable, sellable product. Use when Codex needs to add staging/production deployment structure, CI and release automation, product backlog and roadmap planning, control-plane milestones, or product positioning for a multi-tenant AI gateway such as a FastAPI/PostgreSQL/Redis/S3/SQS stack.
---

# AI Gateway Productization

Use this skill after the basic gateway exists. This skill is for taking a proxy from "working system" to "operable product."

Use `ai-routing-proxy` for core gateway implementation. Use this skill for productization work:

- staging and production environment splits
- release and deployment automation
- rollout and smoke-test workflows
- product backlog, roadmap, and issue shaping
- packaging and positioning
- identifying the next control-plane features needed for pilots

## Workflow

1. Assess current state
2. Decide whether the next step is `deploy`, `operate`, or `sell`
3. Make the smallest repo change that removes the current bottleneck
4. Leave behind a concrete artifact: workflow, manifest, backlog item, roadmap, or doc

## Deploy Track

Use this when the gateway works locally but is not ready for staging or production.

- Split shared deployment artifacts into `base` plus environment overlays
- Keep staging and production separate in config, secrets, namespaces, and replica counts
- Publish immutable images through CI before adding deploy automation
- Prefer deploy workflows that consume existing images instead of rebuilding
- Gate staging deploys on `main`
- Gate production deploys on releases or explicit version inputs
- Add smoke tests after deploy as soon as the environment exists

Read `references/deployment-checklist.md` when planning deployment or release automation.

## Operate Track

Use this when the gateway deploys but is not yet operable by another team.

- Prioritize admin APIs for tenants, API keys, provider configs, and routing policies
- Add RBAC before exposing control-plane endpoints
- Add usage metering and request accounting before dashboards
- Add metrics before dashboards
- Add retries, DLQ handling, and replay paths before claiming audit durability
- Treat secrets managers as the source of truth; GitHub or Kubernetes secrets are transport only

## Sell Track

Use this when the system works technically but lacks a product shape.

- Pick a wedge: compliance, cost control, or multi-tenant governance
- Keep the initial ICP narrow
- Turn architecture gaps into backlog items with acceptance criteria
- Prefer a 90-day roadmap over an aspirational long-term plan
- Package the product in layers: core, team, enterprise

Read `references/product-roadmap.md` when the user wants roadmap, positioning, backlog, or product ideas.

## Backlog Rules

When turning a product direction into backlog items:

- separate `P0`, `P1`, and `P2`
- make every item testable or demoable
- give each item a short goal and explicit acceptance criteria
- keep issue titles implementation-oriented, not vague
- put foundational control-plane and security items ahead of dashboards or polish

## Default Priorities

If the user asks "what next?", bias toward:

1. control-plane CRUD
2. provider hardening
3. admin auth and RBAC
4. usage metering
5. metrics and observability
6. worker reliability
7. deployment automation
8. product UI and polish

## Example Triggers

- "Turn this AI proxy into a product."
- "What do we still need before staging and production?"
- "Create a 90-day roadmap for this gateway."
- "Add deploy workflows and environment overlays."
- "Turn this plan into a backlog."
- "What applications would need this?"
