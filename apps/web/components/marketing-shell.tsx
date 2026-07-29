import type { ReactNode } from "react";
import { AuthControls } from "@/components/auth-controls";

export function ArrowIcon() {
  return (
    <svg
      aria-hidden="true"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M5 12h14" />
      <path d="m13 6 6 6-6 6" />
    </svg>
  );
}

/**
 * Primary navigation. Kept to six items so the bar does not wrap on a laptop;
 * everything else is reachable from the footer, which is the crawlable index of
 * the site.
 */
const PRIMARY_NAV = [
  { href: "/ai-gateway/", label: "AI Gateway" },
  { href: "/architecture/", label: "Architecture" },
  { href: "/salti-b-engine/", label: "SALTI-B" },
  { href: "/ai-governance/", label: "Governance" },
  { href: "/pricing/", label: "Pricing" },
  { href: "/docs/", label: "Docs" },
] as const;

/**
 * The footer is the site's internal link graph. Every indexable page must be
 * reachable from here in one hop, otherwise deep pages depend entirely on the
 * sitemap for discovery — which is a much weaker signal than a real link.
 */
const FOOTER_NAV = [
  {
    title: "Platform",
    links: [
      { href: "/ai-gateway/", label: "AI gateway" },
      { href: "/llm-routing/", label: "LLM routing" },
      { href: "/salti-b-engine/", label: "SALTI-B Engine" },
      { href: "/architecture/", label: "Control architecture" },
      { href: "/integrations/", label: "Integrations" },
    ],
  },
  {
    title: "Governance",
    links: [
      { href: "/ai-governance/", label: "AI governance" },
      { href: "/governed-ai-agents/", label: "Governed agents" },
      { href: "/human-in-the-loop-ai/", label: "Human oversight" },
      { href: "/spatial-intelligence/", label: "Spatial intelligence" },
      { href: "/security/", label: "Security" },
    ],
  },
  {
    title: "Compare",
    links: [
      { href: "/compare/portkey/", label: "vs Portkey" },
      { href: "/compare/litellm/", label: "vs LiteLLM" },
      { href: "/compare/openrouter/", label: "vs OpenRouter" },
      { href: "/glossary/", label: "Glossary" },
      { href: "/docs/", label: "Documentation" },
    ],
  },
  {
    title: "Company",
    links: [
      { href: "/pricing/", label: "Pricing" },
      { href: "/pilot/", label: "Request pilot access" },
      { href: "/contact/", label: "Contact" },
      { href: "/privacy/", label: "Privacy" },
      { href: "/terms/", label: "Terms" },
      { href: "/acceptable-use/", label: "Acceptable use" },
    ],
  },
] as const;

export function MarketingHeader() {
  return (
    <header className="siteHeader">
      <div className="shell headerInner">
        <a className="brand" href="/" aria-label="SALTI8 home">
          SALTI<span>8</span>
        </a>
        <span className="productTag">Layer8 Adaptive</span>
        <nav className="primaryNav" aria-label="Primary navigation">
          {PRIMARY_NAV.map((item) => (
            <a href={item.href} key={item.href}>
              {item.label}
            </a>
          ))}
        </nav>
        <AuthControls />
        <details className="mobileNav">
          <summary aria-label="Open navigation menu">Menu</summary>
          <nav aria-label="Mobile navigation">
            {PRIMARY_NAV.map((item) => (
              <a href={item.href} key={item.href}>
                {item.label}
              </a>
            ))}
            <a href="/sign-in/">Customer login</a>
            <a href="/pilot/">Request access</a>
          </nav>
        </details>
      </div>
    </header>
  );
}

export function FooterNav() {
  return (
    <nav className="footerNav" aria-label="Footer navigation">
      {FOOTER_NAV.map((group) => (
        <div key={group.title}>
          <h2>{group.title}</h2>
          <ul>
            {group.links.map((link) => (
              <li key={link.href}>
                <a href={link.href}>{link.label}</a>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}

export function MarketingFooter() {
  return (
    <footer className="siteFooter">
      <div className="shell footerTop">
        <div className="footerIdentity">
          <a className="brand footerBrand" href="/">
            SALTI<span>8</span>
          </a>
          <p>Industrial precision for governed intelligence.</p>
          <a className="footerCta" href="/pilot/">
            Request pilot access <ArrowIcon />
          </a>
        </div>
        <FooterNav />
      </div>
      <div className="shell footerBottom">
        <div className="footerMeta">
          <span>Layer8 Adaptive by SALTI8</span>
          <span>Powered by the SALTI-B Engine</span>
        </div>
        <p>© 2026 SALTI8 Labs</p>
      </div>
    </footer>
  );
}

export function MarketingPage({ children }: { children: ReactNode }) {
  return (
    <>
      <a className="skipLink" href="#main">
        Skip to content
      </a>
      <MarketingHeader />
      <main id="main">{children}</main>
      <MarketingFooter />
    </>
  );
}
