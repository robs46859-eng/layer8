import type { MetadataRoute } from "next";
import { seoPages } from "@/lib/seo-content";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const pages: MetadataRoute.Sitemap = seoPages
    .filter((page) => !page.noindex)
    .map((page) => ({
      url: `https://salti8.com/${page.slug}/`,
      lastModified: new Date("2026-07-28"),
      changeFrequency: page.slug.startsWith("compare/") ? "monthly" : "weekly",
      priority: page.slug === "ai-gateway" ? 0.9 : 0.7,
    }));
  return [
    {
      url: "https://salti8.com",
      lastModified: new Date("2026-07-28"),
      changeFrequency: "weekly",
      priority: 1,
    },
    ...pages,
  ];
}
