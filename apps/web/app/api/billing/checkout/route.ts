import { customerApi } from "@/lib/customer-api";

export async function POST(request: Request) {
  const body = await request.text();
  return customerApi("/v1/customer/billing/checkout", {
    method: "POST",
    headers: {
      "Idempotency-Key": crypto.randomUUID(),
    },
    body,
  });
}
