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
NEXT_PUBLIC_SITE_URL=https://salti8.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
NEXT_PUBLIC_API_URL=https://api.salti8.com
NEXT_PUBLIC_TEAM_PRICE_LABEL=$99/mo
NEXT_PUBLIC_BUSINESS_PRICE_LABEL=$299/mo
```

`NEXT_PUBLIC_SITE_URL` is the origin baked into every canonical tag, sitemap
entry, `robots.txt` host directive, and JSON-LD `@id`. It must have no trailing
slash. If it is absent the build falls back to `https://salti8.com`, so
production is safe by default — but a staging build without it will advertise
production URLs, which is exactly the duplicate-content problem to avoid.

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

## Server configuration

`apps/web/public/.htaccess` is committed and copied into `out/` by the build.
It is what makes a dumb static host behave correctly: HTTPS and `www` → apex
redirects, trailing-slash enforcement, `ErrorDocument 404 /404.html`, MIME
types for `.webp` and `.webmanifest`, immutable caching for hashed assets, and
security headers.

Do not configure competing redirect rules in hPanel. Two sources of redirect
truth produce redirect chains, and a chain costs both crawl budget and
first-byte time.

## DNS

Hostinger is the DNS authority for `salti8.com`. Required records:

| Type | Name | Value | Purpose |
| --- | --- | --- | --- |
| `A` | `@` | Hostinger site IP (from hPanel) | Apex serves the static site |
| `CNAME` | `www` | `salti8.com` | Resolves, then 301s to apex via `.htaccess` |
| `CNAME` | `api` | Render external hostname for `salti8-api` | Points the API subdomain at Render |
| `TXT` | `@` | Google Search Console verification token | Domain-property verification |
| `CAA` | `@` | `0 issue "letsencrypt.org"` | Restricts who may issue certificates |

The apex must not be a `CNAME` — apex `CNAME` is invalid in standard DNS.
`api.salti8.com` must be a `CNAME` to Render, never an `A` record; Render's
addresses are not static.

TLS is issued by Hostinger for the apex and `www`, and by Render for `api`.
Both certificates must cover their hostname before the first deploy is
announced, or the redirect chain terminates in a certificate warning.

## Required public routes

At minimum, verify:

```text
/
/architecture/
/ai-gateway/
/salti-b-engine/
/ai-governance/
/pricing/
/pilot/
/contact/
/docs/
/glossary/
/privacy/
/terms/
/acceptable-use/
/compare/portkey/
/compare/litellm/
/compare/openrouter/
/sign-in/
/sign-up/
/app/billing/
/billing/success/
/robots.txt
/sitemap.xml
/manifest.webmanifest
/favicon.ico
/404.html
```

`npm run build` asserts every one of these exists in `out/` and fails the build
if one is missing. See `SEO_AND_INDEXING.md` section 5.

Public SEO pages must contain meaningful HTML before JavaScript runs.
Authentication and billing pages must be `noindex`.

## Release verification

1. Confirm the hPanel deployment shows the intended commit and `out` artifact.
2. Confirm the apex domain returns `200` without an `x-nextjs` server runtime.
3. Confirm `www.salti8.com` redirects permanently to `https://salti8.com`.
4. Confirm `http://salti8.com` redirects permanently to HTTPS.
5. Confirm a path without a trailing slash 301s to the slashed form once, with
   no redirect chain.
6. Confirm the routes above return `200`.
7. Confirm an unknown path returns a real `404` status, not `200`.
8. Confirm `/sign-in/` renders the Clerk production instance.
9. Confirm signed-out billing shows a sign-in gate.
10. Submit a clearly labeled internal test contact, then verify it appears in
    the admin pilot-application list.
11. Complete Stripe test Checkout, verify the signed webhook activates the
    organization, and open the customer portal.

A successful build is not sufficient. Any required route returning `503`
blocks release.

## Rollback

Revert the bad commit on `main` and push the revert. Do not rewrite history.
Record the reverted commit, replacement commit, Hostinger deployment
timestamp, and route results.
