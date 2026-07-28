"use client";

import { SignIn } from "@clerk/nextjs";

export function SignInPanel() {
  return (
    <SignIn
      path="/sign-in"
      routing="path"
      forceRedirectUrl="/app/billing/"
      fallbackRedirectUrl="/app/billing/"
      signUpUrl="/sign-up"
    />
  );
}
