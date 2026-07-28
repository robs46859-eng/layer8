import type { Metadata } from "next";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { BillingDashboard } from "@/components/billing-dashboard";

export const metadata: Metadata = {
  title: "Billing & Entitlements",
  description: "Manage Layer8 Adaptive subscription billing and entitlements.",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function BillingPage() {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    redirect("/sign-in");
  }
  const { userId } = await auth();
  if (!userId) {
    redirect("/sign-in");
  }
  return <BillingDashboard />;
}
