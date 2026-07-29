import type { Metadata } from "next";
import { BillingDashboard } from "@/components/billing-dashboard";
import { MarketingPage } from "@/components/marketing-shell";
import {
  businessPriceLabel,
  teamPriceLabel,
} from "@/lib/public-pricing";

export const metadata: Metadata = {
  title: "Billing & Entitlements",
  description: "Manage Layer8 Adaptive subscription billing and entitlements.",
  robots: { index: false, follow: false },
};

export default function BillingPage() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL;
  const clerkConfigured = Boolean(
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,
  );

  if (!apiBaseUrl || !clerkConfigured) {
    return (
      <MarketingPage>
        <section className="contentHero shell compactHero">
          <p className="eyebrow">Customer control plane</p>
          <h1>Billing is awaiting configuration.</h1>
          <p className="contentLead">
            Add the public API URL and Clerk publishable key in Hostinger,
            then rebuild the site to activate customer billing.
          </p>
          <a className="button buttonPrimary" href="/sign-in/">
            Return to sign in
          </a>
        </section>
      </MarketingPage>
    );
  }

  return (
    <BillingDashboard
      apiBaseUrl={apiBaseUrl}
      teamPriceLabel={teamPriceLabel}
      businessPriceLabel={businessPriceLabel}
    />
  );
}
