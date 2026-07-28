import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CheckoutNotice } from "@/components/checkout-notice";
import { ArrowIcon, MarketingPage } from "@/components/marketing-shell";
import { PilotApplicationForm } from "@/components/pilot-application-form";
import {
  pageHref,
  seoPageBySlug,
  seoPages,
  type SeoPage,
} from "@/lib/seo-content";

type PageProps = {
  params: Promise<{ slug: string[] }>;
};

export function generateStaticParams() {
  return seoPages.map((page) => ({ slug: page.slug.split("/") }));
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const key = slug.join("/");
  const page = seoPageBySlug.get(key);
  if (!page) {
    return {};
  }
  const canonical = `/${page.slug}/`;
  return {
    title: page.title,
    description: page.description,
    keywords: page.keywords,
    alternates: { canonical },
    openGraph: {
      type: "website",
      url: canonical,
      title: page.title,
      description: page.description,
      siteName: "SALTI8",
    },
    twitter: {
      card: "summary_large_image",
      title: page.title,
      description: page.description,
    },
    robots: page.noindex
      ? { index: false, follow: false }
      : { index: true, follow: true },
  };
}

function structuredData(page: SeoPage) {
  const breadcrumbs = [
    {
      "@type": "ListItem",
      position: 1,
      name: "SALTI8",
      item: "https://salti8.com",
    },
    {
      "@type": "ListItem",
      position: 2,
      name: page.heading,
      item: `https://salti8.com/${page.slug}/`,
    },
  ];
  const data: Record<string, unknown>[] = [
    {
      "@context": "https://schema.org",
      "@type": "WebPage",
      name: page.title,
      description: page.description,
      url: `https://salti8.com/${page.slug}/`,
      isPartOf: {
        "@type": "WebSite",
        name: "SALTI8",
        url: "https://salti8.com",
      },
      about: {
        "@type": "SoftwareApplication",
        name: "Layer8 Adaptive",
        applicationCategory: "DeveloperApplication",
      },
    },
    {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement: breadcrumbs,
    },
  ];
  if (page.faqs.length) {
    data.push({
      "@context": "https://schema.org",
      "@type": "FAQPage",
      mainEntity: page.faqs.map((faq) => ({
        "@type": "Question",
        name: faq.question,
        acceptedAnswer: {
          "@type": "Answer",
          text: faq.answer,
        },
      })),
    });
  }
  return data;
}

export default async function ContentPage({ params }: PageProps) {
  const { slug } = await params;
  const key = slug.join("/");
  const page = seoPageBySlug.get(key);
  if (!page) {
    notFound();
  }
  const isPilotPage = page.slug === "pilot";

  return (
    <MarketingPage>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(structuredData(page)).replace(/</g, "\\u003c"),
        }}
      />

      <article>
        <header className="contentHero shell">
          <nav className="breadcrumbs" aria-label="Breadcrumb">
            <a href="/">SALTI8</a>
            <span aria-hidden="true">/</span>
            <span>{page.eyebrow}</span>
          </nav>
          <p className="eyebrow">{page.eyebrow}</p>
          <h1>{page.heading}</h1>
          <p className="contentLead">{page.lead}</p>
          <div className="contentActions">
            <a
              className="button buttonPrimary"
              href={isPilotPage ? "#pilot-application" : "/pilot/"}
            >
              Request pilot access <ArrowIcon />
            </a>
            <a className="button buttonSecondary" href="/docs/">
              Read the documentation
            </a>
          </div>
          {page.lastVerified ? (
            <p className="verifiedDate">Pricing last verified: {page.lastVerified}</p>
          ) : null}
        </header>

        {page.slug === "pricing" ? (
          <div className="shell">
            <CheckoutNotice />
          </div>
        ) : null}

        {isPilotPage ? (
          <div className="shell">
            <PilotApplicationForm
              apiBaseUrl={process.env.NEXT_PUBLIC_API_URL}
            />
          </div>
        ) : null}

        <div className="contentBody shell">
          <aside className="contentRail" aria-label="On this page">
            <span>On this page</span>
            {page.sections.map((section, index) => (
              <a key={section.heading} href={`#section-${index + 1}`}>
                {String(index + 1).padStart(2, "0")} · {section.heading}
              </a>
            ))}
            {page.faqs.length ? <a href="#faq">FAQ</a> : null}
          </aside>

          <div className="contentSections">
            {page.sections.map((section, index) => (
              <section id={`section-${index + 1}`} key={section.heading}>
                <span className="sectionNumber">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h2>{section.heading}</h2>
                {section.body.map((paragraph) => (
                  <p key={paragraph}>{paragraph}</p>
                ))}
                {section.points ? (
                  <ul>
                    {section.points.map((point) => (
                      <li key={point}>{point}</li>
                    ))}
                  </ul>
                ) : null}
              </section>
            ))}

            {page.sources?.length ? (
              <section className="sourceBlock" aria-labelledby="sources-title">
                <span className="sectionNumber">Sources</span>
                <h2 id="sources-title">Primary sources</h2>
                <ul>
                  {page.sources.map((source) => (
                    <li key={source.url}>
                      <a href={source.url} rel="noopener noreferrer">
                        {source.label} <ArrowIcon />
                      </a>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            {page.faqs.length ? (
              <section id="faq" className="faqSection">
                <span className="sectionNumber">FAQ</span>
                <h2>Frequently asked questions</h2>
                <div className="faqList">
                  {page.faqs.map((faq) => (
                    <details key={faq.question}>
                      <summary>{faq.question}</summary>
                      <p>{faq.answer}</p>
                    </details>
                  ))}
                </div>
              </section>
            ) : null}
          </div>
        </div>

        <section className="relatedSection">
          <div className="shell">
            <p className="eyebrow">Continue exploring</p>
            <div className="relatedGrid">
              {page.related.map((relatedSlug) => {
                const related = seoPageBySlug.get(relatedSlug);
                if (!related) return null;
                return (
                  <a href={pageHref(related.slug)} key={related.slug}>
                    <span>{related.eyebrow}</span>
                    <strong>{related.heading}</strong>
                    <ArrowIcon />
                  </a>
                );
              })}
            </div>
          </div>
        </section>
      </article>
    </MarketingPage>
  );
}
