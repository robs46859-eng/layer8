import { auth } from "@clerk/nextjs/server";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

export async function customerApi(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    return Response.json(
      { detail: "Customer authentication is not configured" },
      { status: 503 },
    );
  }

  const { getToken, userId, orgId } = await auth();
  if (!userId) {
    return Response.json({ detail: "Sign in required" }, { status: 401 });
  }
  if (!orgId) {
    return Response.json(
      { detail: "Select your customer organization" },
      { status: 403 },
    );
  }

  const token = await getToken();
  if (!token) {
    return Response.json(
      { detail: "Could not create a customer session" },
      { status: 401 },
    );
  }

  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (init.body) {
    headers.set("Content-Type", "application/json");
  }
  return fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}
