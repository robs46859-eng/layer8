# SEO and indexing runbook

**Surface:** `https://salti8.com` (static Next.js export, Hostinger)
**Source:** `apps/web`
**Last updated:** July 29, 2026

This runbook covers how salti8.com is made discoverable, what is deliberately
excluded from the index, and what must be verified before and after a release.
It is the authority for canonical URL shape. If another document disagrees with
this one about URLs, this one wins.

---

## 1. Canonical URL contract

Three things must agree, always. When they drift, Google sees duplicates and
splits ranking signal between them.

| Concern | Value |
| --- | --- |
| Scheme | `https` only — HTTP 301s in `.htaccess` |
| Host | Apex `salti8.com`. `www.salti8.com` 301s to apex |
| Trailing slash | Required. `next.config.ts` sets `trailingSlash: true` |
| Canonical tag | Emitted per page from `alternates.canonical` |
| Sitemap `<loc>` | Built from `absoluteUrl()` in `lib/site.ts` |

`apps/web/lib/site.ts` is the single source of truth. Do not hard-code
`https://salti8.com` anywhere else — import `SITE_URL` or `absoluteUrl()`.

`NEXT_PUBLIC_SITE_URL` overrides the origin at build time. It exists so a
staging build does not advertise production URLs.

---

## 2. What is indexable

Indexable pages are generated from `apps/web/lib/seo-content.ts`. Every entry
in `seoPages` without `noindex: true` gets:

- a static route at `/{slug}/`;
- a `<title>`, meta description, and keyword set;
- a canonical tag;
- Open Graph and Twitter card metadata;
- `WebPage` + `BreadcrumbList` JSON-LD, plus `FAQPage` when `faqs` is non-empty;
- `ImageObject` JSON-LD for every diagram on the page;
- a sitemap entry.

Adding a page means adding one object to `seoPages`. Routes, sitemap entries,
breadcrumbs, and internal "continue exploring" links follow automatically.

### Deliberately excluded

| Path | Mechanism |
| --- | --- |
| `/sign-in/`, `/sign-up/` | `robots: noindex` in page metadata **and** `Disallow` in `robots.txt` |
| `/app/billing/` | same |
| `/billing/success/` | same |
| `/account/`, `/api/` | `Disallow` |

Both controls are used on purpose. `Disallow` stops crawling but does not
remove an already-indexed URL; `noindex` removes it but only if the crawler is
allowed to see the tag. Pages that must never appear carry both, and the
post-build gate fails if any of them leak into the sitemap.

---

## 3. Assets

| Asset | Source | Notes |
| --- | --- | --- |
| `favicon.ico` | `apps/web/app/favicon.ico` | Multi-resolution 16/32/48/64 |
| `icon.png` | `apps/web/app/icon.png` | 512×512 |
| `apple-icon.png` | `apps/web/app/apple-icon.png` | 180×180 |
| `manifest.webmanifest` | `apps/web/app/manifest.ts` | PWA metadata, theme colours |
| Default social card | `public/images/og/salti8-default.png` | **PNG**, 1200×630 |
| Architecture social card | `public/images/og/salti8-architecture.png` | PNG, 1200×630 |
| Architecture diagrams | `public/images/salti8-*.webp` | 1376×736 plus `-sm` half-width variants |

Social cards are PNG, not WebP, on purpose. Several crawlers — LinkedIn in
particular — do not render WebP Open Graph images and will show no preview at
all. Do not "optimise" these to WebP.

Diagrams are served through `<picture>` with a `max-width: 900px` source so
phones do not download the full-width asset. Every `<img>` carries explicit
`width`/`height` so the layout box is reserved before decode; removing those
attributes reintroduces cumulative layout shift.

---

## 4. Server configuration (`apps/web/public/.htaccess`)

`next build` copies `public/` into `out/`, and `scripts/verify-export.mjs`
re-copies `.htaccess` if the dotfile did not survive. The file provides what a
static host cannot infer:

1. HTTPS redirect (checks both `%{HTTPS}` and `X-Forwarded-Proto`);
2. `www` → apex 301;
3. trailing-slash 301 for extension-less paths;
4. `ErrorDocument 404 /404.html`;
5. MIME types for `.webp`, `.avif`, `.webmanifest`, `.woff2`;
6. immutable caching for hashed assets, `max-age=0` for HTML;
7. security headers: HSTS, `X-Content-Type-Options`, `X-Frame-Options`,
   `Referrer-Policy`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`.

Never put a secret in this file. It ships as public content.

---

## 5. Release gate

`npm run build` runs `next build` followed by `scripts/verify-export.mjs`,
which fails the build if any of the following are untrue:

- `out/.htaccess` exists;
- `out/robots.txt`, `out/sitemap.xml`, `out/manifest.webmanifest` exist **as
  files**, not directories (`trailingSlash: true` has turned these into
  directories in past Next releases, which serves the wrong content type);
- every required route exported an `index.html`;
- `out/404.html` exists;
- icons and both social cards exist;
- every `<loc>` in the sitemap corresponds to an exported page;
- no `noindex` path appears in the sitemap.

Run it standalone against an existing build with `npm run verify:export`.

---

## 6. Post-deploy verification

Run after every deploy that touches `apps/web`.

```text
1. https://salti8.com/                      → 200
2. http://salti8.com/                       → 301 to https
3. https://www.salti8.com/                  → 301 to https://salti8.com/
4. https://salti8.com/architecture          → 301 to /architecture/
5. https://salti8.com/architecture/         → 200
6. https://salti8.com/robots.txt            → 200, content-type text/plain
7. https://salti8.com/sitemap.xml           → 200, content-type application/xml
8. https://salti8.com/manifest.webmanifest  → 200
9. https://salti8.com/favicon.ico           → 200
10. https://salti8.com/this-does-not-exist/ → 404 status (not 200 with a 404 page)
11. View source on /architecture/ — headings and body copy must be present
    in the raw HTML before any JavaScript runs
```

Item 10 matters more than it looks: a soft 404 (200 status with "not found"
content) causes Google to index the error page and dilutes crawl budget.

---

## 7. Search Console and Bing

One-time setup, then repeat after any DNS or host migration.

1. **Google Search Console** — add `salti8.com` as a *Domain* property (not a
   URL-prefix property). Domain verification uses a DNS `TXT` record and covers
   every subdomain and scheme at once.
2. Submit `https://salti8.com/sitemap.xml`.
3. Use **URL Inspection → Request indexing** for `/` and `/architecture/` after
   the first deploy that includes them. Do not bulk-request; it is rate limited
   and provides no advantage.
4. **Bing Webmaster Tools** — import the verified Google property, then submit
   the same sitemap. Bing also feeds DuckDuckGo.
5. Check **Coverage** and **Core Web Vitals** one week after launch, then
   monthly.

Expect `/sign-in/`, `/sign-up/`, `/app/billing/` and `/billing/success/` to be
reported as *Excluded by robots.txt* or *Excluded by noindex*. That is the
intended state, not an error to fix.

---

## 8. Secondary hosts (Vercel preview)

`apps/web/.vercel/project.json` links this directory to the Vercel project
`layer8-web`. Any Vercel deployment publishes a full copy of the site at a
`*.vercel.app` hostname, which is a duplicate of production.

Two controls keep that from splitting ranking signal:

1. Set `NEXT_PUBLIC_SITE_URL=https://salti8.com` in the Vercel project's
   environment for **all** environments. Every page on the `*.vercel.app` copy
   then emits a canonical pointing at production, which is the correct
   cross-domain canonical pattern.
2. Enable **Vercel Deployment Protection** (Settings → Deployment Protection) so
   preview URLs require authentication and are never crawlable.

`apps/web/vercel.json` sets `outputDirectory: "out"` and `trailingSlash: true`
to match `next.config.ts`. The previous value of `.next` was wrong for an
`output: "export"` build and would have deployed the wrong directory.

Do not point `salti8.com` at both Hostinger and Vercel. One apex, one host.

## 9. Content maintenance

- Comparison pages (`/compare/*`) cite third-party pricing. Re-verify quarterly
  and update `lastVerified`; stale competitor pricing is both a trust problem
  and a legal exposure.
- `lastUpdated` on a page drives its sitemap `lastmod`. Set it when the content
  materially changes, not on every deploy — a `lastmod` that moves on every
  build trains crawlers to ignore the field entirely.
- `DEFAULT_LAST_MODIFIED` in `app/sitemap.ts` is the fallback for pages with no
  declared date. Bump it deliberately, in a content commit.

---

## 10. Related documents

- `HOSTINGER_DEPLOYMENT.md` — build settings, environment, and DNS
- `../architecture/DEPLOYED_BUILD_BLUEPRINT.md` — what is actually deployed
- `../design/ENTERPRISE_DESIGN_DIRECTIVE.md` — visual and copy standards
