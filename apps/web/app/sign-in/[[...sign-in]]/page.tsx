import type { Metadata } from "next";
import { MarketingPage } from "@/components/marketing-shell";
import { SignInPanel } from "@/components/sign-in-panel";

export const metadata: Metadata = {
  title: "Customer Sign In",
  description: "Sign in to your Layer8 Adaptive customer account.",
  robots: { index: false, follow: false },
};

export default function CustomerSignInPage() {
  return (
    <MarketingPage>
      <section className="authShell shell">
        <div className="authCopy">
          <p className="eyebrow">Customer access</p>
          <h1>Enter the governed workspace.</h1>
          <p>
            Sign in to review subscription status, entitlements, and
            self-service billing for your Layer8 Adaptive organization.
          </p>
        </div>
        <SignInPanel />
      </section>
    </MarketingPage>
  );
}
