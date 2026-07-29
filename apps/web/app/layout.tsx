import type { Metadata, Viewport } from "next";
import { Barlow, Barlow_Condensed } from "next/font/google";
import { ClerkClientProvider } from "@/components/clerk-client-provider";
import {
  DEFAULT_OG_IMAGE,
  ORG_LEGAL_NAME,
  PRODUCT_NAME,
  SITE_NAME,
  SITE_URL,
  absoluteUrl,
} from "@/lib/site";
import "./globals.css";

const barlow = Barlow({
  variable: "--font-barlow",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  display: "swap",
});

const barlowCondensed = Barlow_Condensed({
  variable: "--font-barlow-condensed",
  subsets: ["latin"],
  weight: ["400", "600"],
  display: "swap",
});

const siteDescription =
  "Layer8 Adaptive by SALTI8 is a governed AI execution platform for multi-provider routing, durable agent cascades, bounded repair, human approval, and auditable provenance.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "SALTI8 | Governed AI Execution",
    template: "%s | SALTI8",
  },
  description: siteDescription,
  applicationName: PRODUCT_NAME,
  authors: [{ name: ORG_LEGAL_NAME, url: SITE_URL }],
  creator: ORG_LEGAL_NAME,
  publisher: ORG_LEGAL_NAME,
  category: "technology",
  keywords: [
    "AI gateway",
    "LLM gateway",
    "AI model routing",
    "AI governance",
    "governed AI agents",
    "LLM observability",
    "human-in-the-loop AI",
    "durable AI workflows",
    "adaptive spatial intelligence",
  ],
  alternates: {
    canonical: "/",
  },
  formatDetection: {
    telephone: false,
    address: false,
    email: false,
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: absoluteUrl("/"),
    siteName: SITE_NAME,
    title: "SALTI8 | Governed AI Execution",
    description: siteDescription,
    images: [DEFAULT_OG_IMAGE],
  },
  twitter: {
    card: "summary_large_image",
    title: "SALTI8 | Governed AI Execution",
    description: siteDescription,
    images: [DEFAULT_OG_IMAGE.url],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },
};

export const viewport: Viewport = {
  colorScheme: "light dark",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f4f0e8" },
    { media: "(prefers-color-scheme: dark)", color: "#161c1f" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${barlow.variable} ${barlowCondensed.variable}`}
    >
      <body>
        <ClerkClientProvider>{children}</ClerkClientProvider>
      </body>
    </html>
  );
}
