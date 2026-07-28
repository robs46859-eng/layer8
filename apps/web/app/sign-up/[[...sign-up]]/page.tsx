import { SignUp } from "@clerk/nextjs";
import type { Metadata } from "next";
import { MarketingPage } from "@/components/marketing-shell";

export const metadata: Metadata = {
  title: "Create Customer Account",
  description: "Create your Layer8 Adaptive customer account.",
  robots: { index: false, follow: false },
};

export default function CustomerSignUpPage() {
  return (
    <MarketingPage>
      <section className="authShell shell">
        <div className="authCopy">
          <p className="eyebrow">Customer registration</p>
          <h1>Create your governed workspace.</h1>
          <p>
            Create an account to start onboarding your Layer8 Adaptive
            organization.
          </p>
        </div>
        <SignUp
          path="/sign-up"
          routing="path"
          signInUrl="/sign-in"
          forceRedirectUrl="/app/billing/"
          fallbackRedirectUrl="/app/billing/"
        />
      </section>
    </MarketingPage>
  );
}
