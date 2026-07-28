"use client";

import { OrganizationSwitcher, UserButton } from "@clerk/nextjs";
import { useCallback, useEffect, useState } from "react";

type BillingAccount = {
  tenant_id: string;
  plan_key: string;
  subscription_status: string;
  cancel_at_period_end: boolean;
  current_period_end: string | null;
  entitlements: string[];
};

function readError(payload: unknown): string {
  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload &&
    typeof payload.detail === "string"
  ) {
    return payload.detail;
  }
  return "The billing service could not complete that request.";
}

export function BillingDashboard() {
  const [account, setAccount] = useState<BillingAccount | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState("");

  const refresh = useCallback(async () => {
    setError("");
    const response = await fetch("/api/billing/status", { cache: "no-store" });
    const payload = (await response.json()) as BillingAccount | { detail?: string };
    if (!response.ok) {
      setError(readError(payload));
      return;
    }
    setAccount(payload as BillingAccount);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function openBilling(path: "checkout" | "portal", planKey?: string) {
    setPending(path);
    setError("");
    const response = await fetch(`/api/billing/${path}`, {
      method: "POST",
      headers: planKey ? { "Content-Type": "application/json" } : undefined,
      body: planKey ? JSON.stringify({ plan_key: planKey }) : undefined,
    });
    const payload = (await response.json()) as {
      checkout_url?: string;
      portal_url?: string;
      detail?: string;
    };
    setPending("");
    if (!response.ok) {
      setError(readError(payload));
      return;
    }
    const url = payload.checkout_url ?? payload.portal_url;
    if (url) {
      window.location.assign(url);
    }
  }

  return (
    <main className="accountShell">
      <header className="accountHeader">
        <a className="brand" href="/" aria-label="SALTI8 home">
          SALTI<span>8</span>
        </a>
        <div className="accountIdentity">
          <OrganizationSwitcher hidePersonal />
          <UserButton />
        </div>
      </header>

      <section className="shell accountContent">
        <div className="accountHeading">
          <p className="eyebrow">Customer control plane</p>
          <h1>Billing &amp; entitlements</h1>
          <p>
            Subscription access is granted only after a signed Stripe webhook
            updates your organization.
          </p>
        </div>

        {error ? <p className="accountError">{error}</p> : null}

        <div className="billingGrid">
          <section className="billingStatus">
            <span>Current plan</span>
            <strong>{account?.plan_key ?? "Loading"}</strong>
            <dl>
              <div>
                <dt>Status</dt>
                <dd>{account?.subscription_status ?? "Checking"}</dd>
              </div>
              <div>
                <dt>Renews</dt>
                <dd>
                  {account?.current_period_end
                    ? new Date(account.current_period_end).toLocaleDateString()
                    : "Not scheduled"}
                </dd>
              </div>
            </dl>
            {account?.subscription_status !== "inactive" ? (
              <button
                className="button buttonSecondary"
                disabled={Boolean(pending)}
                onClick={() => void openBilling("portal")}
              >
                {pending === "portal" ? "Opening…" : "Manage in Stripe"}
              </button>
            ) : null}
          </section>

          <section className="billingPlans">
            <p className="eyebrow">Activate a paid workspace</p>
            <div>
              <article>
                <span>Team</span>
                <strong>Governed routing</strong>
                <button
                  className="button buttonPrimary"
                  disabled={Boolean(pending)}
                  onClick={() => void openBilling("checkout", "team")}
                >
                  Choose Team
                </button>
              </article>
              <article>
                <span>Business</span>
                <strong>Extended controls</strong>
                <button
                  className="button buttonPrimary"
                  disabled={Boolean(pending)}
                  onClick={() => void openBilling("checkout", "business")}
                >
                  Choose Business
                </button>
              </article>
            </div>
          </section>
        </div>

        <section className="entitlementList">
          <p className="eyebrow">Active entitlements</p>
          {account?.entitlements?.length ? (
            <ul>
              {account.entitlements.map((entitlement) => (
                <li key={entitlement}>{entitlement.replaceAll("_", " ")}</li>
              ))}
            </ul>
          ) : (
            <p>No paid entitlements have been provisioned yet.</p>
          )}
        </section>
      </section>
    </main>
  );
}
