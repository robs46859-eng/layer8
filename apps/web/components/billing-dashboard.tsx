"use client";

import {
  CreateOrganization,
  OrganizationSwitcher,
  UserButton,
  useAuth,
} from "@clerk/react";
import { useCallback, useEffect, useState } from "react";

type BillingAccount = {
  tenant_id: string;
  plan_key: string;
  subscription_status: string;
  cancel_at_period_end: boolean;
  current_period_end: string | null;
  entitlements: string[];
};

type CustomerApiKey = {
  id: string;
  prefix: string;
  scopes: string[];
  status: string;
  created_at: string;
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

async function readPayload(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type");
  if (!contentType?.includes("application/json")) {
    return null;
  }
  return response.json();
}

function stripeRedirectUrl(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const candidate =
    ("checkout_url" in payload && typeof payload.checkout_url === "string"
      ? payload.checkout_url
      : null) ??
    ("portal_url" in payload && typeof payload.portal_url === "string"
      ? payload.portal_url
      : null);
  if (!candidate) {
    return null;
  }
  try {
    const url = new URL(candidate);
    if (
      url.protocol === "https:" &&
      (url.hostname === "checkout.stripe.com" ||
        url.hostname === "billing.stripe.com")
    ) {
      return url.toString();
    }
  } catch {
    return null;
  }
  return null;
}

function AccountHeader({ showIdentity = true }: { showIdentity?: boolean }) {
  return (
    <header className="accountHeader">
      <a className="brand" href="/" aria-label="SALTI8 home">
        SALTI<span>8</span>
      </a>
      {showIdentity ? (
        <div className="accountIdentity">
          <OrganizationSwitcher
            hidePersonal
            afterCreateOrganizationUrl="/app/billing/"
            afterSelectOrganizationUrl="/app/billing/"
          />
          <UserButton />
        </div>
      ) : null}
    </header>
  );
}

function AccountGate({
  children,
  eyebrow,
  heading,
}: {
  children: React.ReactNode;
  eyebrow: string;
  heading: string;
}) {
  return (
    <main className="accountShell">
      <AccountHeader />
      <section className="shell accountContent">
        <div className="accountHeading">
          <p className="eyebrow">{eyebrow}</p>
          <h1>{heading}</h1>
          {children}
        </div>
      </section>
    </main>
  );
}

export function BillingDashboard({
  apiBaseUrl,
  businessPriceLabel,
  teamPriceLabel,
}: {
  apiBaseUrl: string;
  businessPriceLabel?: string;
  teamPriceLabel?: string;
}) {
  const { getToken, isLoaded, isSignedIn, orgId } = useAuth();
  const [account, setAccount] = useState<BillingAccount | null>(null);
  const [apiKeys, setApiKeys] = useState<CustomerApiKey[]>([]);
  const [newApiKey, setNewApiKey] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState("");
  const normalizedApiBaseUrl = apiBaseUrl.replace(/\/+$/, "");

  const customerRequest = useCallback(
    async (path: string, init: RequestInit = {}) => {
      if (!isLoaded || !isSignedIn) {
        throw new Error("Sign in is required to access billing.");
      }
      if (!orgId) {
        throw new Error("Select your customer organization to access billing.");
      }
      const token = await getToken();
      if (!token) {
        throw new Error("Could not create a customer session.");
      }

      const headers = new Headers(init.headers);
      headers.set("Accept", "application/json");
      headers.set("Authorization", `Bearer ${token}`);
      if (init.body) {
        headers.set("Content-Type", "application/json");
      }

      return fetch(`${normalizedApiBaseUrl}${path}`, {
        ...init,
        headers,
        cache: "no-store",
      });
    },
    [getToken, isLoaded, isSignedIn, normalizedApiBaseUrl, orgId],
  );

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !orgId) {
      setAccount(null);
      setError("");
      return;
    }

    let current = true;
    setAccount(null);
    setError("");
    void customerRequest("/v1/customer/billing")
      .then(async (response) => {
        const payload = await readPayload(response);
        if (!response.ok) {
          throw new Error(readError(payload));
        }
        if (current) {
          setAccount(payload as BillingAccount);
        }
      })
      .catch((reason: unknown) => {
        if (current) {
          setError(
            reason instanceof Error
              ? reason.message
              : "The billing service could not be reached.",
          );
        }
      });
    return () => {
      current = false;
    };
  }, [customerRequest, isLoaded, isSignedIn, orgId]);

  useEffect(() => {
    if (
      !account ||
      !["active", "trialing", "past_due"].includes(account.subscription_status) ||
      !account.entitlements.includes("api_access")
    ) {
      setApiKeys([]);
      return;
    }

    let current = true;
    void customerRequest("/v1/customer/billing/api-keys")
      .then(async (response) => {
        const payload = await readPayload(response);
        if (!response.ok) {
          throw new Error(readError(payload));
        }
        if (current) {
          setApiKeys(payload as CustomerApiKey[]);
        }
      })
      .catch((reason: unknown) => {
        if (current) {
          setError(
            reason instanceof Error
              ? reason.message
              : "Your API keys could not be loaded.",
          );
        }
      });
    return () => {
      current = false;
    };
  }, [account, customerRequest]);

  async function openBilling(path: "checkout" | "portal", planKey?: string) {
    setPending(path);
    setError("");
    try {
      const response = await customerRequest(
        `/v1/customer/billing/${path}`,
        {
          method: "POST",
          headers:
            path === "checkout"
              ? { "Idempotency-Key": crypto.randomUUID() }
              : undefined,
          body: planKey ? JSON.stringify({ plan_key: planKey }) : undefined,
        },
      );
      const payload = await readPayload(response);
      if (!response.ok) {
        throw new Error(readError(payload));
      }
      const url = stripeRedirectUrl(payload);
      if (!url) {
        throw new Error("The billing service returned an invalid Stripe URL.");
      }
      window.location.assign(url);
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The billing service could not be reached.",
      );
    } finally {
      setPending("");
    }
  }

  async function createApiKey() {
    setPending("api-key");
    setError("");
    setNewApiKey("");
    try {
      const response = await customerRequest(
        "/v1/customer/billing/api-keys",
        { method: "POST" },
      );
      const payload = await readPayload(response);
      if (!response.ok) {
        throw new Error(readError(payload));
      }
      const created = payload as CustomerApiKey & { api_key?: string };
      if (!created.api_key) {
        throw new Error("The API service did not return a new key.");
      }
      setApiKeys((current) => [...current, created]);
      setNewApiKey(created.api_key);
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Your API key could not be created.",
      );
    } finally {
      setPending("");
    }
  }

  if (!isLoaded) {
    return (
      <AccountGate eyebrow="Customer control plane" heading="Loading account.">
        <p>Clerk is confirming your customer session.</p>
      </AccountGate>
    );
  }

  if (!isSignedIn) {
    return (
      <AccountGate eyebrow="Customer control plane" heading="Sign in required.">
        <p>
          Customer billing is private. Sign in before reviewing subscription
          status or entitlements.
        </p>
        <a className="button buttonPrimary accountGateAction" href="/sign-in/">
          Sign in
        </a>
      </AccountGate>
    );
  }

  if (!orgId) {
    return (
      <AccountGate
        eyebrow="Create your workspace"
        heading="One step before checkout."
      >
        <p>
          Name your workspace to create its private Layer8 tenant automatically.
          You can use your own name if you are signing up individually.
        </p>
        <CreateOrganization
          afterCreateOrganizationUrl="/app/billing/"
          skipInvitationScreen
        />
      </AccountGate>
    );
  }

  return (
    <main className="accountShell">
      <AccountHeader />

      <section
        className="shell accountContent"
        aria-busy={Boolean(pending) || (!account && !error)}
      >
        <div className="accountHeading">
          <p className="eyebrow">Customer control plane</p>
          <h1>Billing &amp; entitlements</h1>
          <p>
            Subscription access is granted only after a signed Stripe webhook
            updates your organization.
          </p>
        </div>

        {error ? (
          <p className="accountError" role="alert" aria-live="assertive">
            {error}
          </p>
        ) : null}
        <p className="accountStatus" role="status" aria-live="polite">
          {pending === "checkout"
            ? "Opening secure Stripe Checkout…"
            : pending === "portal"
              ? "Opening the Stripe customer portal…"
              : !account && !error
                ? "Loading subscription status…"
                : ""}
        </p>

        <div className="billingGrid">
          <section className="billingStatus">
            <span>Current plan</span>
            <strong>{account?.plan_key ?? (error ? "Unavailable" : "Loading")}</strong>
            <dl>
              <div>
                <dt>Status</dt>
                <dd>{account?.subscription_status ?? "Checking"}</dd>
              </div>
              <div>
                <dt>
                  {account?.cancel_at_period_end ? "Access until" : "Renews"}
                </dt>
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
                <p className="planPrice">
                  {teamPriceLabel?.trim() || "Price confirmed in Stripe"}
                </p>
                <button
                  className="button buttonPrimary"
                  disabled={Boolean(pending)}
                  aria-label={`Choose Team plan${
                    teamPriceLabel?.trim()
                      ? ` at ${teamPriceLabel.trim()}`
                      : ""
                  }`}
                  onClick={() => void openBilling("checkout", "team")}
                >
                  Choose Team
                </button>
              </article>
              <article>
                <span>Business</span>
                <strong>Extended controls</strong>
                <p className="planPrice">
                  {businessPriceLabel?.trim() || "Price confirmed in Stripe"}
                </p>
                <button
                  className="button buttonPrimary"
                  disabled={Boolean(pending)}
                  aria-label={`Choose Business plan${
                    businessPriceLabel?.trim()
                      ? ` at ${businessPriceLabel.trim()}`
                      : ""
                  }`}
                  onClick={() => void openBilling("checkout", "business")}
                >
                  Choose Business
                </button>
              </article>
            </div>
            <p className="billingLegal">
              By choosing a plan, you agree to the{" "}
              <a href="/terms/" target="_blank" rel="noreferrer">
                Terms of Service
              </a>
              ,{" "}
              <a href="/privacy/" target="_blank" rel="noreferrer">
                Privacy Notice
              </a>
              , and{" "}
              <a href="/acceptable-use/" target="_blank" rel="noreferrer">
                Acceptable Use Policy
              </a>
              . Subscriptions renew monthly until canceled.
            </p>
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

        {account?.entitlements.includes("api_access") ? (
          <section className="entitlementList">
            <p className="eyebrow">API access</p>
            <h2>Connect your first application.</h2>
            <p>
              Create a scoped API key after payment. The complete key is shown
              once; store it in your application&apos;s secret manager.
            </p>
            {apiKeys.length ? (
              <ul>
                {apiKeys.map((apiKey) => (
                  <li key={apiKey.id}>
                    {apiKey.prefix} · {apiKey.status}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No API keys have been created.</p>
            )}
            {newApiKey ? (
              <div className="authNotice" role="status">
                <strong>Copy this key now. It will not be shown again.</strong>
                <code>{newApiKey}</code>
              </div>
            ) : null}
            <button
              className="button buttonPrimary"
              disabled={Boolean(pending) || apiKeys.filter((key) => key.status === "active").length >= 2}
              onClick={() => void createApiKey()}
            >
              {pending === "api-key" ? "Creating…" : "Create API key"}
            </button>
          </section>
        ) : null}
      </section>
    </main>
  );
}
