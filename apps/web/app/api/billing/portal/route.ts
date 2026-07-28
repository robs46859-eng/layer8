import { customerApi } from "@/lib/customer-api";

export async function POST() {
  return customerApi("/v1/customer/billing/portal", {
    method: "POST",
  });
}
