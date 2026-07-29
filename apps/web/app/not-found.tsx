import type { Metadata } from "next";
import { ArrowIcon, MarketingPage } from "@/components/marketing-shell";

export const metadata: Metadata = {
  title: "Page not found",
  description:
    "That SALTI8 page does not exist. Use the links below to reach the AI gateway, SALTI-B Engine, architecture, governance, pricing, or documentation.",
  robots: { index: false, follow: true },
  // Without this the page inherits the root layout's canonical and declares
  // itself a duplicate of the home page, which is how 404s get treated as soft
  // 200s in Search Console.
  alternates: { canonical: null },
};

const destinations = [
  {
    href: "/",
    label: "Home",
    detail: "The governed execution overview.",
  },
  {
    href: "/architecture/",
    label: "Architecture",
    detail: "Layer8, SALTI, and B-HDSR in one control stack.",
  },
  {
    href: "/ai-gateway/",
    label: "AI gateway",
    detail: "Multi-provider routing under one policy layer.",
  },
  {
    href: "/salti-b-engine/",
    label: "SALTI-B Engine",
    detail: "Validation, bounded repair, and acceptance gates.",
  },
  {
    href: "/ai-governance/",
    label: "AI governance",
    detail: "Policy, approval, and auditable provenance.",
  },
  {
    href: "/pricing/",
    label: "Pricing",
    detail: "Plans and what each entitlement includes.",
  },
  {
    href: "/docs/",
    label: "Documentation",
    detail: "Integration and operational reference.",
  },
  {
    href: "/contact/",
    label: "Contact",
    detail: "Reach the SALTI8 team directly.",
  },
];

export default function NotFound() {
  return (
    <MarketingPage>
      <section className="contentHero shell compactHero">
        <p className="eyebrow">404 · Route not found</p>
        <h1>That page is not part of the deployed site.</h1>
        <p className="contentLead">
          The address may be out of date, mistyped, or from a build that is no
          longer published. Nothing is broken on your side — the routes below
          are the current public surface.
        </p>
        <div className="contentActions">
          <a className="button buttonPrimary" href="/">
            Return home <ArrowIcon />
          </a>
          <a className="button buttonSecondary" href="/contact/">
            Report a broken link
          </a>
        </div>
      </section>

      <section className="relatedSection">
        <div className="shell">
          <p className="eyebrow">Where you probably meant to go</p>
          <div className="relatedGrid">
            {destinations.map((item) => (
              <a href={item.href} key={item.href}>
                <span>{item.label}</span>
                <strong>{item.detail}</strong>
                <ArrowIcon />
              </a>
            ))}
          </div>
        </div>
      </section>
    </MarketingPage>
  );
}
