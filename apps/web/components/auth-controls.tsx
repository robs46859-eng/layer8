"use client";

import {
  Show,
  SignInButton,
  SignUpButton,
  UserButton,
} from "@clerk/nextjs";

export function AuthControls() {
  return (
    <div className="authControls" aria-label="Account controls">
      <Show when="signed-out">
        <SignInButton mode="redirect">
          <button className="headerAction" type="button">
            Customer login <span aria-hidden="true">→</span>
          </button>
        </SignInButton>
        <SignUpButton mode="redirect">
          <button className="headerAction authSignUp" type="button">
            Create account
          </button>
        </SignUpButton>
      </Show>
      <Show when="signed-in">
        <UserButton />
      </Show>
    </div>
  );
}
