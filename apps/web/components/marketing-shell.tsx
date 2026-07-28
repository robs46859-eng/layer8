import type { ReactNode } from "react";

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

export function MarketingHeader() {
  return (
    <header className="siteHeader">
      <div className="shell headerInner">
        <a className="brand" href="/" aria-label="SALTI8 home">
          SALTI<span>8</span>
        </a>
        <span className="productTag">Layer8 Adaptive</span>
        <nav aria-label="Primary navigation">
          <a href="/ai-gateway">AI Gateway</a>
          <a href="/salti-b-engine">SALTI-B</a>
          <a href="/ai-governance">Governance</a>
          <a href="/pricing">Pricing</a>
          <a href="/docs">Docs</a>
        </nav>
        <a className="headerAction" href="/sign-in">
          Customer login <ArrowIcon />
        </a>
      </div>
    </header>
  );
}

export function MarketingFooter() {
  return (
    <footer className="siteFooter">
      <div className="shell footerInner">
        <div>
          <a className="brand footerBrand" href="/">
            SALTI<span>8</span>
          </a>
          <p>Industrial precision for governed intelligence.</p>
        </div>
        <div className="footerLinks">
          <a href="/ai-gateway">AI Gateway</a>
          <a href="/llm-routing">LLM Routing</a>
          <a href="/governed-ai-agents">Governed Agents</a>
          <a href="/human-in-the-loop-ai">Human Oversight</a>
          <a href="/security">Security</a>
          <a href="/glossary">Glossary</a>
        </div>
        <div className="footerMeta">
          <span>Layer8 Adaptive by SALTI8</span>
          <span>Powered by the SALTI-B Engine</span>
          <span>© 2026 SALTI8 Labs</span>
        </div>
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
