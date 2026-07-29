import type { Metadata } from "next";
import { MarketingPage } from "@/components/marketing-shell";
import { SignUpPanel } from "@/components/sign-up-panel";

export const metadata: Metadata = {
  title: "Create Customer Account",
  description: "Create your Layer8 Adaptive customer account.",
  robots: { index: false, follow: false },
};

export default function CustomerSignUpPage() {
  const clerkConfigured = Boolean(
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,
  );

  return (
    <MarketingPage>
      <section className="authShell shell">
        <div className="authCopy">
          <p className="eyebrow">Customer registration</p>
          <h1>Create your governed workspace.</h1>
          <p>
            Registration is for invited customer administrators. If you do not
            have an invitation, request pilot access first.
          </p>
          <a className="textLink" href="/pilot/">
            Request pilot access
          </a>
        </div>
        {clerkConfigured ? (
          <SignUpPanel />
        ) : (
          <div className="authNotice" role="status">
            Customer registration is awaiting the Clerk publishable key.
          </div>
        )}
      </section>
    </MarketingPage>
  );
}
