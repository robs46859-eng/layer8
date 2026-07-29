"use client";

import {
  useAuth,
  UserButton,
} from "@clerk/react";

function AuthLinks() {
  return (
    <div className="authControls" aria-label="Account controls">
      <a className="headerAction" href="/sign-in/">
        Customer login <span aria-hidden="true">→</span>
      </a>
      <a className="headerAction authSignUp" href="/pilot/">
        Request access
      </a>
    </div>
  );
}

function ClerkAuthControls() {
  const { isLoaded, isSignedIn } = useAuth();

  if (!isLoaded || !isSignedIn) {
    return <AuthLinks />;
  }

  return (
    <div className="authControls" aria-label="Account controls">
      <UserButton />
    </div>
  );
}

export function AuthControls() {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    return <AuthLinks />;
  }

  return <ClerkAuthControls />;
}
