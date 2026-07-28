import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/app/", "/account/", "/api/"],
      },
    ],
    sitemap: "https://salti8.com/sitemap.xml",
    host: "https://salti8.com",
  };
}
