import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

export const dynamic = "force-static";

/**
 * Authenticated and transactional surfaces are excluded here *and* carry
 * `robots: noindex` in their page metadata. Disallow alone does not remove a
 * URL from the index if it is linked externally, so both controls are kept.
 */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: [
          "/app/",
          "/account/",
          "/api/",
          "/sign-in/",
          "/sign-up/",
          "/billing/",
        ],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
