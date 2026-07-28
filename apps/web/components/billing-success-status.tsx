"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";

type BillingAccount = {
  plan_key: string;
  subscription_status: string;
  entitlements: string[];
};

type PollState = {
  kind: "checking" | "ready" | "pending" | "error" | "signed-out" | "no-org";
  message: string;
  account?: BillingAccount;
};

const activeStatuses = new Set(["active", "trialing"]);

function errorDetail(payload: unknown): string {
  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload &&
    typeof payload.detail === "string"
  ) {
    return payload.detail;
  }
  return "Subscription status could not be loaded.";
}

export function BillingSuccessStatus({
  apiBaseUrl,
}: {
  apiBaseUrl: string;
}) {
  const { getToken, isLoaded, isSignedIn, orgId } = useAuth();
  const [refreshKey, setRefreshKey] = useState(0);
  const [pollState, setPollState] = useState<PollState>({
    kind: "checking",
    message: "Confirming your subscription with the signed Stripe webhook…",
  });
  const normalizedApiBaseUrl = apiBaseUrl.replace(/\/+$/, "");

  useEffect(() => {
    if (!isLoaded) {
      setPollState({
        kind: "checking",
        message: "Confirming your customer session…",
      });
      return;
    }
    if (!isSignedIn) {
      setPollState({
        kind: "signed-out",
        message: "Sign in to confirm subscription status for your workspace.",
      });
      return;
    }
    if (!orgId) {
      setPollState({
        kind: "no-org",
        message:
          "Select the organization used at checkout to confirm its subscription.",
      });
      return;
    }

    let disposed = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;

    async function poll() {
      attempt += 1;
      try {
        const token = await getToken();
        if (!token) {
          throw new Error("Could not create a customer session.");
        }
        const response = await fetch(
          `${normalizedApiBaseUrl}/v1/customer/billing`,
          {
            headers: {
              Accept: "application/json",
              Authorization: `Bearer ${token}`,
            },
            cache: "no-store",
          },
        );
        const payload = (await response.json().catch(() => null)) as
          | BillingAccount
          | { detail?: string }
          | null;
        if (!response.ok) {
          throw new Error(errorDetail(payload));
        }

        const account = payload as BillingAccount;
        if (activeStatuses.has(account.subscription_status)) {
          if (!disposed) {
            setPollState({
              kind: "ready",
              message:
                "Subscription confirmed. Your paid entitlements are active.",
              account,
            });
          }
          return;
        }

        if (attempt < 16) {
          if (!disposed) {
            setPollState({
              kind: "checking",
              message:
                "Checkout returned successfully. Waiting for the signed Stripe webhook…",
              account,
            });
            timer = setTimeout(() => void poll(), 2500);
          }
          return;
        }

        if (!disposed) {
          setPollState({
            kind: "pending",
            message:
              "Stripe confirmation is still processing. Check again or open billing in a moment.",
            account,
          });
        }
      } catch (reason: unknown) {
        if (!disposed) {
          setPollState({
            kind: "error",
            message:
              reason instanceof Error
                ? reason.message
                : "Subscription status could not be loaded.",
          });
        }
      }
    }

    setPollState({
      kind: "checking",
      message: "Confirming your subscription with the signed Stripe webhook…",
    });
    void poll();

    return () => {
      disposed = true;
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [
    getToken,
    isLoaded,
    isSignedIn,
    normalizedApiBaseUrl,
    orgId,
    refreshKey,
  ]);

  const isError = pollState.kind === "error";
  const isChecking = pollState.kind === "checking";

  return (
    <section
      className={`billingConfirmation billingConfirmation-${pollState.kind}`}
      role={isError ? "alert" : "status"}
      aria-live={isError ? "assertive" : "polite"}
      aria-busy={isChecking}
    >
      <p>{pollState.message}</p>
      {pollState.account ? (
        <dl>
          <div>
            <dt>Plan</dt>
            <dd>{pollState.account.plan_key}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{pollState.account.subscription_status}</dd>
          </div>
        </dl>
      ) : null}
      <div className="contentActions">
        {pollState.kind === "signed-out" ? (
          <a className="button buttonPrimary" href="/sign-in/">
            Sign in
          </a>
        ) : (
          <button
            className="button buttonSecondary"
            type="button"
            disabled={isChecking}
            onClick={() => setRefreshKey((key) => key + 1)}
          >
            {isChecking ? "Checking…" : "Check again"}
          </button>
        )}
        <a className="button buttonPrimary" href="/app/billing/">
          Open customer billing
        </a>
      </div>
    </section>
  );
}
