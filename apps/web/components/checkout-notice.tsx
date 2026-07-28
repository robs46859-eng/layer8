"use client";

import { useEffect, useState } from "react";

export function CheckoutNotice() {
  const [cancelled, setCancelled] = useState(false);

  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    setCancelled(query.get("checkout") === "cancelled");
  }, []);

  if (!cancelled) {
    return null;
  }

  return (
    <aside className="checkoutNotice" role="alert" aria-live="assertive">
      <strong>Checkout was canceled.</strong>
      <p>
        No subscription change was made. Return to customer billing whenever
        you are ready to choose a plan.
      </p>
      <a className="button buttonSecondary" href="/app/billing/">
        Return to billing
      </a>
    </aside>
  );
}
