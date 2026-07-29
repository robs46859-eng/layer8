/**
 * Single source of truth for absolute URLs.
 *
 * Every canonical, sitemap entry, robots directive, and JSON-LD `@id` must be
 * derived from here. Hard-coding `https://salti8.com` in more than one place is
 * how duplicate-content and split-signal indexing problems start.
 *
 * `NEXT_PUBLIC_SITE_URL` is a build-time value on Hostinger. The fallback keeps
 * local development and CI deterministic.
 */
const RAW_SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://salti8.com";

/** Absolute origin with no trailing slash, e.g. `https://salti8.com`. */
export const SITE_URL = RAW_SITE_URL.replace(/\/+$/, "");

export const SITE_NAME = "SALTI8";
export const PRODUCT_NAME = "Layer8 Adaptive";
export const ORG_LEGAL_NAME = "SALTI8 Labs";

/**
 * The site is exported with `trailingSlash: true`. Canonicals must match the
 * URL the host actually serves, so every path helper appends the slash.
 */
export function absoluteUrl(path = "/"): string {
  if (!path || path === "/") {
    return `${SITE_URL}/`;
  }
  const clean = path.replace(/^\/+/, "").replace(/\/+$/, "");
  return `${SITE_URL}/${clean}/`;
}

/** Default social card. PNG, 1200x630 — WebP is not reliably rendered by all crawlers. */
export const DEFAULT_OG_IMAGE = {
  url: "/images/og/salti8-default.png",
  width: 1200,
  height: 630,
  alt: "SALTI8 — Layer8 Adaptive, governed AI execution. Every AI action enters through policy.",
} as const;

export const ARCHITECTURE_OG_IMAGE = {
  url: "/images/og/salti8-architecture.png",
  width: 1200,
  height: 630,
  alt: "The Layer8, SALTI, and B-HDSR control stack for governed adaptability.",
} as const;
