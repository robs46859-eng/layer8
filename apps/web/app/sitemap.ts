import type { MetadataRoute } from "next";
import { seoPages, type SeoPage } from "@/lib/seo-content";
import { absoluteUrl } from "@/lib/site";

export const dynamic = "force-static";

/**
 * Fallback modification date for pages that do not declare their own.
 * Kept as an explicit constant so the export stays byte-deterministic between
 * builds — a sitemap whose `lastmod` changes on every deploy trains crawlers to
 * ignore the field.
 */
const DEFAULT_LAST_MODIFIED = "2026-07-29";

/** Highest-intent commercial and definitional pages. */
const PRIORITY_OVERRIDES: Record<string, number> = {
  "ai-gateway": 0.9,
  architecture: 0.9,
  "salti-b-engine": 0.85,
  "ai-governance": 0.85,
  "llm-routing": 0.85,
  pricing: 0.8,
  pilot: 0.8,
  docs: 0.7,
  glossary: 0.6,
  contact: 0.5,
  privacy: 0.3,
  terms: 0.3,
  "acceptable-use": 0.3,
};

function lastModified(page: SeoPage): Date {
  const declared = page.lastUpdated ?? page.lastVerified;
  if (declared) {
    const parsed = new Date(declared);
    if (!Number.isNaN(parsed.getTime())) {
      return parsed;
    }
  }
  return new Date(DEFAULT_LAST_MODIFIED);
}

function changeFrequency(page: SeoPage): "monthly" | "weekly" | "yearly" {
  if (page.slug.startsWith("compare/")) return "monthly";
  if (["privacy", "terms", "acceptable-use"].includes(page.slug)) return "yearly";
  return "weekly";
}

export default function sitemap(): MetadataRoute.Sitemap {
  const pages: MetadataRoute.Sitemap = seoPages
    .filter((page) => !page.noindex)
    .map((page) => ({
      url: absoluteUrl(page.slug),
      lastModified: lastModified(page),
      changeFrequency: changeFrequency(page),
      priority: PRIORITY_OVERRIDES[page.slug] ?? 0.6,
    }));

  return [
    {
      // Trailing slash matters: it must match the canonical the page emits,
      // otherwise the sitemap advertises a URL that redirects.
      url: absoluteUrl("/"),
      lastModified: new Date(DEFAULT_LAST_MODIFIED),
      changeFrequency: "weekly",
      priority: 1,
    },
    ...pages,
  ];
}
