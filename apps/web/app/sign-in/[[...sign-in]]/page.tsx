import type { Metadata } from "next";
import { SignIn } from "@clerk/nextjs";
import { MarketingPage } from "@/components/marketing-shell";

export const metadata: Metadata = {
  title: "Customer Sign In",
  description: "Sign in to your Layer8 Adaptive customer account.",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default function SignInPage() {
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
        {process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ? (
          <SignIn
            routing="path"
            path="/sign-in"
            forceRedirectUrl="/app/billing"
            signUpUrl="/pilot"
          />
        ) : (
          <div className="authNotice">
            Customer login is ready for deployment. Add the Clerk environment
            keys to activate it.
          </div>
        )}
      </section>
    </MarketingPage>
  );
}
