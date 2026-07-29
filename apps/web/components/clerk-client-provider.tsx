"use client";

import { ClerkProvider } from "@clerk/react";

export function ClerkClientProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  if (!publishableKey) {
    return children;
  }

  return (
    <ClerkProvider
      publishableKey={publishableKey}
      signInUrl="/sign-in/"
      signUpUrl="/sign-up/"
      signInFallbackRedirectUrl="/app/billing/"
      signUpFallbackRedirectUrl="/app/billing/"
    >
      {children}
    </ClerkProvider>
  );
}
