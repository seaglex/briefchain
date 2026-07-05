/**
 * Server-side authentication and API utilities.
 *
 * This module imports `next/headers` and MUST only be imported from Server
 * Components or API Route handlers. Do NOT import it into Client Components.
 */

import { cookies } from "next/headers";
import { API_BASE_URL, parseBackendError, SESSION_COOKIE_NAME } from "./auth";

/** Read the session token from the httpOnly cookie. Only usable server-side. */
export async function getSessionToken(): Promise<string | undefined> {
  const cookieStore = await cookies();
  return cookieStore.get(SESSION_COOKIE_NAME)?.value;
}

/** Server-side authenticated fetch helper. */
export async function serverFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<{ ok: true; data: T } | { ok: false; status: number; message: string }> {
  const token = await getSessionToken();
  if (!token) {
    return { ok: false, status: 401, message: "未登录" };
  }

  const url = path.startsWith("http") ? path : `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const { message } = await parseBackendError(response);
    return { ok: false, status: response.status, message };
  }

  if (response.status === 204) {
    return { ok: true, data: undefined as T };
  }

  const data = (await response.json()) as T;
  return { ok: true, data };
}

/** Fetch the current authenticated user profile. Only usable server-side. */
export async function getCurrentUser(): Promise<
  | { ok: true; user: { id: string; name: string; email: string | null; phone: string | null; user_type: string } }
  | { ok: false; message: string }
> {
  const result = await serverFetch<{
    id: string;
    name: string;
    email: string | null;
    phone: string | null;
    user_type: string;
  }>("/api/v1/auth/me");

  if (!result.ok) {
    return { ok: false, message: result.message };
  }

  return { ok: true, user: result.data };
}

/** Proxy a request from a Next.js API Route to the backend using the session cookie. */
export async function proxyWithToken(
  backendPath: string,
  request: Request,
  method?: string
): Promise<Response> {
  const token = await getSessionToken();
  if (!token) {
    return Response.json(
      { error: { code: "UNAUTHORIZED", message: "未登录" } },
      { status: 401 }
    );
  }

  const url = `${API_BASE_URL}${backendPath}`;
  const actualMethod = method || request.method;
  let body: BodyInit | undefined;
  if (actualMethod !== "GET" && actualMethod !== "HEAD") {
    body = await request.text();
  }

  const response = await fetch(url, {
    method: actualMethod,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body,
  });

  const responseBody = await response.text();
  return new Response(responseBody, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}

/** Read the brief_id associated with an invite token. Public, no auth required. */
export async function getInviteBriefId(token: string): Promise<string | null> {
  const response = await fetch(`${API_BASE_URL}/api/v1/invites/${token}`);
  if (!response.ok) return null;
  const data = (await response.json()) as { brief?: { brief_id?: string } };
  return data.brief?.brief_id ?? null;
}

/** Proxy a request from a Next.js API Route to a backend public endpoint (no auth). */
export async function proxyWithoutToken(
  backendPath: string,
  request: Request,
  method?: string
): Promise<Response> {
  const url = `${API_BASE_URL}${backendPath}`;
  const actualMethod = method || request.method;
  let body: BodyInit | undefined;
  if (actualMethod !== "GET" && actualMethod !== "HEAD") {
    body = await request.text();
  }

  const response = await fetch(url, {
    method: actualMethod,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
    },
    body,
  });

  const responseBody = await response.text();
  return new Response(responseBody, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}
