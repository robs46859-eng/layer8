# Hostinger web deployment

> **Superseded for launch:** The persistent Next.js runtime described below
> builds successfully but fails on the current Hostinger environment because
> Node aborts while creating its worker thread. Do not redeploy this
> configuration. Follow
> [`SALTI8_LAUNCH_ACTION_PLAN.md`](./SALTI8_LAUNCH_ACTION_PLAN.md) for the
> static Hostinger frontend, Hostinger DNS, external FastAPI service, Clerk,
> and Stripe recovery sequence.

The repository root is a Hostinger-compatible Node.js application. The
Hostinger app should connect directly to
`https://github.com/robs46859-eng/layer8` on `main`; do not clone it into a
second repository.

## Build settings

```text
Node.js version: 22
Root directory: apps/web
Build command: npm run build
Framework: Next.js
Output directory: .next
```

The Next build emits a conventional production build. The post-build
preparation step places the installed runtime dependencies and public assets
inside `.next`, which is the output root required by Hostinger's native
Next.js runner.

## Hostinger environment

```text
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
NEXT_PUBLIC_API_URL=https://api.salti8.com
```

Attach `salti8.com` and `www.salti8.com` to the app and make one canonical
host redirect to the other. A push to `main` triggers automatic redeployment
after the GitHub integration is connected.

## Separate API deployment

Hostinger's Node.js web application runs the Next.js site and server-side
billing bridge. The Python API, PostgreSQL migrations, Redis, object storage,
queue, and Stripe webhook must run on the container/Kubernetes deployment
described under `deploy/`. Point `api.salti8.com` to that service before
enabling the live webhook.

Never add Stripe secret keys, the webhook secret, the Clerk JWT private secret,
provider keys, or the Layer8 admin token to client-visible variables.
