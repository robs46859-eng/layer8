"use client";

import { SignUp } from "@clerk/react";

export function SignUpPanel() {
  return (
    <SignUp
      routing="hash"
      signInUrl="/sign-in/"
      forceRedirectUrl="/app/billing/"
      fallbackRedirectUrl="/app/billing/"
    />
  );
}
