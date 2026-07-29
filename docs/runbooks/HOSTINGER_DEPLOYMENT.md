# Hostinger static deployment

Hostinger is the DNS authority, CDN, TLS endpoint, and static host for
`salti8.com`. It must not run the SALTI8 website as a persistent Node.js
process.

The previous server-side Next.js configuration is superseded. Hostinger's
Node 22 runtime aborted before application startup while creating a worker
thread, which produced public `503` responses even after successful builds.

## Git source

```text
Repository: robs46859-eng/layer8
Branch: main
Root directory: apps/web
Automatic deployment: enabled
```

Use the existing `salti8.com` website entry. Do not create another Hostinger
website or repository.

## Build settings

```text
Framework: Other / Static
Node.js version: 22.x
Root directory: apps/web
Install command: npm ci
Build command: npm run build
Output directory: out
Entry file / start command: none
```

`next build` uses `output: "export"` and produces `apps/web/out`. Every route
Hostinger serves is a file; there is no `.next/standalone` process.

## Hostinger environment

Hostinger needs only public, build-time values:

```text
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
NEXT_PUBLIC_API_URL=https://api.salti8.com
NEXT_PUBLIC_TEAM_PRICE_LABEL=$99/mo
NEXT_PUBLIC_BUSINESS_PRICE_LABEL=$299/mo
```

Never add these backend values to Hostinger:

```text
CLERK_SECRET_KEY
CLERK_JWT_KEY
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
DATABASE_URL
REDIS_URL
AWS credentials
ADMIN_API_TOKEN
provider API keys
```

## Required public routes

At minimum, verify:

```text
/
/pricing/
/pilot/
/contact/
/privacy/
/terms/
/acceptable-use/
/sign-in/
/sign-up/
/app/billing/
/billing/success/
/robots.txt
/sitemap.xml
```

Public SEO pages must contain meaningful HTML before JavaScript runs.
Authentication and billing pages must be `noindex`.

## Release verification

1. Confirm the hPanel deployment shows the intended commit and `out` artifact.
2. Confirm the apex domain returns `200` without an `x-nextjs` server runtime.
3. Confirm `www.salti8.com` redirects permanently to `https://salti8.com`.
4. Confirm the routes above return `200`.
5. Confirm `/sign-in/` renders the Clerk production instance.
6. Confirm signed-out billing shows a sign-in gate.
7. Submit a clearly labeled internal test contact, then verify it appears in
   the admin pilot-application list.
8. Complete Stripe test Checkout, verify the signed webhook activates the
   organization, and open the customer portal.

A successful build is not sufficient. Any required route returning `503`
blocks release.

## Rollback

Revert the bad commit on `main` and push the revert. Do not rewrite history.
Record the reverted commit, replacement commit, Hostinger deployment
timestamp, and route results.
