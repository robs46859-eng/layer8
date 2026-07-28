# Hostinger web deployment

The repository root is a Hostinger-compatible Node.js application. The
Hostinger app should connect directly to
`https://github.com/robs46859-eng/layer8` on `main`; do not clone it into a
second repository.

## Build settings

```text
Node.js version: 22
Root directory: apps/web
Build command: npm run build
Framework: Other
Output directory: .next/standalone
Entry file: server.js
```

The Next build emits a self-contained standalone server with traced runtime
dependencies. The post-build preparation step copies public assets and Next
static assets into the standalone application directory.

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
