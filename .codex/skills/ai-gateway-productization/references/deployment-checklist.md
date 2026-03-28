# Deployment Checklist

Use this when moving an AI gateway from local/dev to staged or production deployment.

## Image and Release Path

- CI publishes immutable images
- release workflow publishes semver tags
- deploy workflows consume published images instead of rebuilding
- staging uses `latest` or a branch image
- production uses explicit version tags

## Environment Split

- separate staging and production config
- separate namespaces
- separate buckets and queues
- separate databases and Redis instances
- separate secrets

## Kubernetes Shape

- `base/` contains shared API, worker, and service manifests
- overlays set namespace, config, replicas, and image tag
- secret examples should never be treated as production secret storage

## GitHub Environment Inputs

- base64 kubeconfig per environment
- secret manifest or external secret configuration per environment
- protected production environment where appropriate

## Post-Deploy Checks

- `/healthz`
- `/readyz`
- one authenticated inference request
- rollout completion for API and worker

## Before Production

- admin auth and RBAC exist
- secret-manager path exists
- metrics are scraped
- worker retry and DLQ behavior is defined
- rollback path is documented
