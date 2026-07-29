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
import {
  DEFAULT_OG_IMAGE,
  PRODUCT_NAME,
  SITE_NAME,
  SITE_URL,
  absoluteUrl,
} from "@/lib/site";

type PageProps = {
  params: Promise<{ slug: string[] }>;
};

export const dynamicParams = false;

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
  const ogImage = page.ogImage
    ? { url: page.ogImage, width: 1200, height: 630, alt: page.title }
    : DEFAULT_OG_IMAGE;
  return {
    title: page.title,
    description: page.description,
    keywords: page.keywords,
    alternates: { canonical },
    openGraph: {
      type: "article",
      locale: "en_US",
      url: absoluteUrl(page.slug),
      title: page.title,
      description: page.description,
      siteName: SITE_NAME,
      images: [ogImage],
    },
    twitter: {
      card: "summary_large_image",
      title: page.title,
      description: page.description,
      images: [ogImage.url],
    },
    robots: page.noindex
      ? { index: false, follow: false }
      : {
          index: true,
          follow: true,
          googleBot: {
            index: true,
            follow: true,
            "max-image-preview": "large",
            "max-snippet": -1,
          },
        },
  };
}

/**
 * Compare pages live one level deeper (`/compare/portkey/`), so the breadcrumb
 * trail has to reflect that. A flat two-item trail on a nested URL is a
 * mismatch Google will quietly drop.
 */
function breadcrumbTrail(page: SeoPage) {
  const trail = [
    {
      "@type": "ListItem",
      position: 1,
      name: SITE_NAME,
      item: absoluteUrl("/"),
    },
  ];
  const segments = page.slug.split("/");
  if (segments.length > 1) {
    trail.push({
      "@type": "ListItem",
      position: 2,
      name: "Comparisons",
      item: absoluteUrl(segments[0]),
    });
  }
  trail.push({
    "@type": "ListItem",
    position: trail.length + 1,
    name: page.heading,
    item: absoluteUrl(page.slug),
  });
  return trail;
}

function structuredData(page: SeoPage) {
  const pageUrl = absoluteUrl(page.slug);
  const figures = [
    ...(page.heroFigure ? [page.heroFigure] : []),
    ...page.sections.flatMap((section) =>
      section.figure ? [section.figure] : [],
    ),
  ];

  const data: Record<string, unknown>[] = [
    {
      "@context": "https://schema.org",
      "@type": "WebPage",
      "@id": `${pageUrl}#webpage`,
      name: page.title,
      description: page.description,
      url: pageUrl,
      inLanguage: "en-US",
      ...(page.lastUpdated ? { dateModified: page.lastUpdated } : {}),
      isPartOf: {
        "@type": "WebSite",
        name: SITE_NAME,
        url: absoluteUrl("/"),
      },
      publisher: {
        "@type": "Organization",
        name: SITE_NAME,
        url: absoluteUrl("/"),
      },
      about: {
        "@type": "SoftwareApplication",
        name: PRODUCT_NAME,
        applicationCategory: "DeveloperApplication",
      },
      // Declaring the images here is what makes them eligible for Google Images
      // against this page rather than as orphaned assets.
      ...(figures.length
        ? {
            primaryImageOfPage: {
              "@type": "ImageObject",
              contentUrl: `${SITE_URL}${figures[0].src}`,
              caption: figures[0].caption,
              width: figures[0].width,
              height: figures[0].height,
            },
            image: figures.map((figure) => ({
              "@type": "ImageObject",
              contentUrl: `${SITE_URL}${figure.src}`,
              caption: figure.caption,
              description: figure.alt,
              width: figure.width,
              height: figure.height,
            })),
          }
        : {}),
    },
    {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement: breadcrumbTrail(page),
    },
  ];

  if (page.faqs.length) {
    data.push({
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "@id": `${pageUrl}#faq`,
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

/**
 * Diagrams are served as plain <picture>/<img> rather than next/image because
 * the site is a static export with `images.unoptimized: true` — next/image adds
 * a wrapper and no optimisation here. Explicit width/height reserve the box so
 * the diagram cannot shift text that has already painted.
 */
function SectionDiagram({
  figure,
  eager = false,
}: {
  figure: NonNullable<SeoPage["sections"][number]["figure"]>;
  eager?: boolean;
}) {
  return (
    <figure className="sectionFigure">
      <picture>
        {figure.srcSmall ? (
          <source
            media="(max-width: 900px)"
            srcSet={figure.srcSmall}
            type="image/webp"
          />
        ) : null}
        <img
          src={figure.src}
          alt={figure.alt}
          width={figure.width}
          height={figure.height}
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          fetchPriority={eager ? "high" : "auto"}
        />
      </picture>
      <figcaption>{figure.caption}</figcaption>
    </figure>
  );
}

export default async function ContentPage({ params }: PageProps) {
  const { slug } = await params;
  const key = slug.join("/");
  const page = seoPageBySlug.get(key);
  if (!page) {
    notFound();
  }
  const isPilotPage = page.slug === "pilot";
  const isContactPage = page.slug === "contact";
  const isPricingPage = page.slug === "pricing";
  const isLegalPage = [
    "privacy",
    "terms",
    "acceptable-use",
  ].includes(page.slug);

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
              href={
                isPilotPage
                  ? "#pilot-application"
                  : isPricingPage
                    ? "/app/billing/"
                  : isContactPage
                    ? "#contact-form"
                    : isLegalPage
                      ? "/contact/"
                      : "/pilot/"
              }
            >
              {isPricingPage
                ? "Open customer billing"
                : isContactPage || isLegalPage
                  ? "Contact SALTI8"
                  : "Request pilot access"}{" "}
              <ArrowIcon />
            </a>
            <a className="button buttonSecondary" href="/docs/">
              Read the documentation
            </a>
          </div>
          {page.lastVerified ? (
            <p className="verifiedDate">Pricing last verified: {page.lastVerified}</p>
          ) : null}
          {page.lastUpdated ? (
            <p className="verifiedDate">Last updated: {page.lastUpdated}</p>
          ) : null}
        </header>

        {page.heroFigure ? (
          <div className="shell heroFigureShell">
            <SectionDiagram figure={page.heroFigure} eager />
          </div>
        ) : null}

        {page.slug === "pricing" ? (
          <div className="shell">
            <CheckoutNotice />
          </div>
        ) : null}

        {isPilotPage || isContactPage ? (
          <div className="shell">
            <PilotApplicationForm
              apiBaseUrl={process.env.NEXT_PUBLIC_API_URL}
              purpose={isContactPage ? "contact" : "pilot"}
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
                {section.figure ? (
                  <SectionDiagram figure={section.figure} eager={index === 0} />
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
