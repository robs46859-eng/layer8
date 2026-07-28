import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata, Viewport } from "next";
import { Barlow, Barlow_Condensed } from "next/font/google";
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
  metadataBase: new URL("https://salti8.com"),
  title: {
    default: "SALTI8 | Governed AI Execution",
    template: "%s | SALTI8",
  },
  description: siteDescription,
  applicationName: "Layer8 Adaptive",
  keywords: [
    "AI gateway",
    "LLM gateway",
    "AI model routing",
    "AI governance",
    "governed AI agents",
    "LLM observability",
    "human-in-the-loop AI",
    "durable AI workflows",
  ],
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    url: "/",
    siteName: "SALTI8",
    title: "SALTI8 | Governed AI Execution",
    description: siteDescription,
    images: [
      {
        url: "/images/salti8-acrylic-architecture.webp",
        width: 2000,
        height: 1091,
        alt: "SALTI8 acrylic architecture representing governed AI execution layers.",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "SALTI8 | Governed AI Execution",
    description: siteDescription,
    images: ["/images/salti8-acrylic-architecture.webp"],
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
        <ClerkProvider>{children}</ClerkProvider>
      </body>
    </html>
  );
}
