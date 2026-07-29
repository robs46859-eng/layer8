import type { Metadata } from "next";
import { BillingSuccessStatus } from "@/components/billing-success-status";
import { MarketingPage } from "@/components/marketing-shell";

export const metadata: Metadata = {
  title: "Subscription Received",
  description: "Your Layer8 Adaptive subscription checkout has completed.",
  robots: { index: false, follow: false },
};

export default function BillingSuccessPage() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL;
  const clerkConfigured = Boolean(
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,
  );

  return (
    <MarketingPage>
      <section className="contentHero shell compactHero">
        <p className="eyebrow">Billing confirmation</p>
        <h1>Checkout completed.</h1>
        <p className="contentLead">
          Stripe has returned you to SALTI8. Access is provisioned from the
          signed webhook event—not from this browser redirect. Your tenant
          administrator can confirm subscription status in Layer8 Adaptive.
        </p>
        {apiBaseUrl && clerkConfigured ? (
          <BillingSuccessStatus apiBaseUrl={apiBaseUrl} />
        ) : (
          <div className="authNotice">
            Subscription verification is awaiting the public API URL.
          </div>
        )}
      </section>
    </MarketingPage>
  );
}
