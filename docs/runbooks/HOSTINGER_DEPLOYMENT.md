# Hostinger Next.js deployment

Hostinger runs the SALTI8 website as a server-side Next.js application.
Layer8's FastAPI control plane, Stripe webhook, database, cache, and audit
worker run separately from the web application.

## Git source

```text
Repository: robs46859-eng/layer8
Branch: main
Automatic deployment: enabled
```

Use the existing `salti8.com` website entry. Do not create another website or
temporary Hostinger domain for a deployment retry.

## hPanel build settings

```text
Framework: Next.js
Node.js version: 22.x
Root directory: apps/web
Build and output settings: Default
Build command: npm run build
Output directory: .next
Start command: npm run start
```

`next build` generates `.next`. This is a server application, not a static
export, because Clerk's Next.js provider, proxy, sign-in, and sign-up routes
require the Next.js runtime.

## Hostinger environment

Hostinger needs only the web application's settings:

```text
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
NEXT_PUBLIC_API_URL=https://api.salti8.com
NEXT_PUBLIC_TEAM_PRICE_LABEL=$99/mo
NEXT_PUBLIC_BUSINESS_PRICE_LABEL=$299/mo
```

`NEXT_PUBLIC_*` values are embedded during the build and require a redeploy
after a change.

Do not store these backend-only values in Hostinger:

```text
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_LIVE_MODE
STRIPE_PRICE_TEAM_MONTHLY
STRIPE_PRICE_BUSINESS_MONTHLY
STRIPE_PORTAL_CONFIGURATION_ID
CLERK_JWT_KEY
CLERK_ISSUER
DATABASE_URL
REDIS_URL
AWS credentials
```

Those values belong to the `salti8-api` service declared in `render.yaml`.

## Expected routes

After a successful build, Hostinger must serve:

```text
/
/pricing
/sign-in
/sign-up
/app/billing
/billing/success
/robots.txt
/sitemap.xml
```

Signed-out visitors may access the marketing, sign-in, and sign-up routes.
`/app/billing` and `/billing/success` must redirect to Clerk sign-in.

## Post-deploy verification

1. Confirm hPanel reports the expected commit and a completed deployment.
2. Check a unique cache-busting homepage URL and both canonical hosts.
3. Confirm `/sign-in` and `/sign-up` render Clerk's production instance.
4. Confirm `/app/billing` redirects signed-out visitors.
5. Sign in and confirm the browser can reach `https://api.salti8.com`.
6. Create a test Checkout before attempting a live payment.
7. Confirm Stripe delivers a signed webhook and Layer8 grants entitlements.
8. Open the Stripe customer portal from the billing page.

A completed Hostinger build is not sufficient evidence. Any required route
returning Hostinger's generic 503 blocks release.

## Troubleshooting

If the build fails, inspect the final deployment-log error and reproduce with:

```bash
npm ci
npm run check
npm run build
```

If the build succeeds but the website returns 503:

1. Inspect Hostinger runtime logs.
2. Inspect the hosting plan's maximum-process and memory graphs.
3. Confirm there is only one SALTI8 Node.js website.
4. Confirm Node 22, `apps/web`, Next.js, and default `.next` output.
5. Restart the existing application; do not create another website.

## Rollback

Revert the bad commit on `main` and push the revert. Do not rewrite history.
Record the reverted commit, replacement commit, Hostinger deployment timestamp,
and the post-rollback route results.
