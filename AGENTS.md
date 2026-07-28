# Layer8 Adaptive Repository Instructions

These instructions apply to the entire repository. More specific `AGENTS.md`
files may add local guidance, but they must not weaken the SEO, accessibility,
security, or verification requirements below.

## Product and Brand

- Company/umbrella brand: **Castoreum Labs**.
- Primary product: **Layer8 Adaptive**.
- Core reasoning and orchestration engine: **SALTI-B**.
- Primary domain candidate: `castoreum.io`.
- Describe the product as a governed AI execution platform: multi-provider
  routing, durable cascades, validation, bounded repair, human approval,
  provenance, auditability, and spatial-intelligence workflows.
- Do not reduce the positioning to a generic LLM proxy or make unsupported
  claims about compliance, accuracy, savings, customers, or performance.

## Source of Truth

- Follow `docs/architecture/PLATFORM_BUILD_PLAN.md` for the target architecture
  and delivery sequence.
- The original frontend reference files are in the sibling project directory
  `../Layer8 and SALTI-B Platform`. Preserve their visual language and content
  intent while rebuilding them as maintainable production components.
- Do not copy generated dependencies, build output, credentials, or secrets
  from the reference directory.
- Keep public marketing content, authenticated product UI, API services, and
  background workers independently deployable.

## SEO Is a Release Requirement

SEO must be designed into every public page from its first implementation.
Do not defer it to a later marketing phase.

### Rendering and Crawlability

- Public marketing, pricing, comparison, resource, glossary, integration, and
  documentation pages must be server-rendered or statically generated.
- Critical copy, headings, links, pricing, and structured data must be present
  in the initial HTML response. Do not require client-side JavaScript for
  discovery or indexing.
- Authenticated application pages, account pages, internal search results,
  preview environments, and duplicate/filter URLs must be `noindex`.
- Maintain valid `robots.txt` and XML sitemaps. Include only canonical,
  indexable, successful URLs in sitemaps.
- Use stable, descriptive, lowercase URLs with hyphens. Avoid opaque IDs and
  query parameters on indexable pages.
- Set one canonical URL per public page. Use permanent redirects when public
  URLs change and return accurate 404 or 410 responses for removed content.
- Add `hreflang` only when real localized equivalents exist.

### Information Architecture

Plan navigation and internal links around these page groups:

- Home
- Product: AI gateway, routing, durable cascades, validation and repair,
  governance, human approval, observability, spatial intelligence
- Solutions: engineering, platform teams, regulated operations, and
  multi-agent workflows
- Integrations: model providers, data systems, observability, identity, and
  deployment platforms
- Pricing
- Documentation and API reference
- Security and trust
- Customer stories when verified examples exist
- Resources, blog, glossary, and frequently asked questions
- Competitor and alternative pages based on verifiable, current facts

Every important page must be reachable through contextual internal links, not
only through a sitemap. Use breadcrumbs on nested content.

### Search Themes

Write for user intent and topical authority, not keyword density. Relevant
themes include:

- AI gateway and LLM gateway
- multi-provider AI gateway
- AI model routing and failover
- AI governance and audit logs
- LLM observability
- governed AI agents
- human-in-the-loop AI
- multi-tenant AI gateway
- durable AI workflows and bounded repair
- spatial intelligence workflows
- alternatives and comparisons for relevant AI gateway products

Use clear language, examples, diagrams, API snippets, and original evidence.
Do not create thin programmatic pages, doorway pages, repetitive city pages,
keyword-stuffed copy, or pages whose only purpose is capturing search traffic.

### On-Page Requirements

Every indexable page must have:

- A unique, descriptive HTML title and meta description.
- Exactly one clear page-level `h1`, followed by a logical heading hierarchy.
- A self-referencing canonical URL.
- Useful Open Graph and social-sharing metadata.
- Semantic HTML, descriptive link text, and meaningful image alternative text.
- Contextual links to related product, documentation, and resource pages.
- A visible author or responsible organization and an accurate updated date
  for editorial content.

Prefer titles that communicate the page's primary intent in roughly 45–60
characters and descriptions that summarize its value in roughly 140–160
characters. Treat these as editorial targets, not reasons to truncate useful
language.

### Structured Data

- Emit valid JSON-LD only when it matches visible page content.
- Use the most specific applicable types, such as `Organization`, `WebSite`,
  `SoftwareApplication`, `Product`, `BreadcrumbList`, `Article`, and
  `TechArticle`.
- Use `FAQPage` only for genuine, visible FAQs and only when current search
  engine policies permit it.
- Never fabricate ratings, reviews, prices, authors, customers, or company
  details for structured data.
- Validate changed structured data before release.

### Comparison and Pricing Content

- Use official competitor sources for product and pricing claims.
- Record a visible "last verified" date and link to the primary source.
- Clearly distinguish free tiers, platform fees, usage charges, model inference
  costs, annual commitments, and custom enterprise pricing.
- State when a price is unavailable rather than estimating it.
- Keep comparisons factual and respectful. Do not use competitor trademarks in
  a way that implies affiliation.
- Re-verify time-sensitive claims before publishing or materially updating a
  comparison page.

## Performance and Accessibility

- Target Core Web Vitals at the 75th percentile: LCP at or below 2.5 seconds,
  INP at or below 200 milliseconds, and CLS at or below 0.1.
- Set image dimensions, use responsive modern formats, and lazy-load only
  below-the-fold media.
- Minimize client JavaScript on public pages. Code-split interactive tools and
  avoid third-party scripts that block rendering.
- Self-host or efficiently preload only necessary font files and provide
  sensible system fallbacks.
- Meet WCAG 2.2 AA: keyboard access, visible focus, adequate contrast, labels,
  landmarks, reduced-motion support, and correct semantics.
- Preserve readable content and core navigation when JavaScript fails.

## Content and Documentation Quality

- Answer the user's question early; avoid vague hero copy and unsubstantiated
  superlatives.
- Explain how Layer8 works, who it is for, its limitations, and how it differs.
- Public API documentation must be crawlable, versioned, linkable at the
  heading level, and include safe copyable examples.
- Never place real API keys, credentials, personal data, or production secrets
  in content or examples.
- Give diagrams and images nearby explanatory text so their meaning is
  accessible to users and search engines.

## Analytics and Measurement

- Configure webmaster/search-console verification and a privacy-conscious
  analytics implementation per environment.
- Track meaningful outcomes such as demo requests, account creation, pricing
  engagement, documentation use, and qualified contact submissions.
- Keep campaign parameters out of canonical URLs.
- Respect consent requirements and Do Not Track or equivalent product policy.
- Analytics failure must never prevent the page from rendering or accepting a
  form submission.

## Engineering Conventions

- Prefer typed, reusable components and keep page-specific content separate
  from shared layout and design-system code.
- Centralize metadata, canonical URL construction, structured data, sitemap
  generation, and robots rules to prevent drift.
- Use one source of truth for public routes, navigation, and sitemap entries.
- Preserve the reference frontend's distinctive visual design; do not replace
  it with generic template styling.
- Add tests for metadata helpers, canonical URLs, sitemap inclusion/exclusion,
  structured data, redirects, and public-page server rendering.

## Public-Site Definition of Done

A public-facing change is not complete until:

- The page renders meaningful HTML without client JavaScript.
- The title, description, canonical, robots directive, social metadata, and
  heading hierarchy are correct.
- Structured data, if present, validates and matches visible content.
- The page is correctly included in or excluded from the sitemap.
- Internal links work and no new broken links are introduced.
- Mobile and desktop layouts pass visual review.
- Keyboard navigation and automated accessibility checks pass.
- Performance remains within the project's agreed budgets.
- Tests, linting, type checks, and the production build pass.
- Pricing, comparison, security, and compliance claims have primary-source
  support and a current verification date.

When a requirement cannot be met, document the reason and impact in the pull
request or commit handoff rather than silently omitting it.
