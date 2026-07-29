import type { MetadataRoute } from "next";
import { PRODUCT_NAME, SITE_NAME } from "@/lib/site";

export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: `${SITE_NAME} — ${PRODUCT_NAME}`,
    short_name: SITE_NAME,
    description:
      "Governed AI execution: multi-provider routing, durable agent cascades, bounded repair, human approval, and auditable provenance.",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: "#161c1f",
    theme_color: "#161c1f",
    icons: [
      {
        src: "/images/salti8-mark-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/images/salti8-mark-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
    ],
  };
}
