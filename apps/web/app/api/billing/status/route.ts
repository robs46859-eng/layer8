import { customerApi } from "@/lib/customer-api";

export async function GET() {
  return customerApi("/v1/customer/billing");
}
