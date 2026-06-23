/**
 * Shared authentication utilities for BriefChain frontend.
 *
 * This module provides client-safe helpers. Server-only helpers that depend on
 * `next/headers` live in `lib/server-auth.ts` to avoid importing Node-only APIs
 * into Client Components.
 */

/** Name of the httpOnly session cookie managed by Next.js API routes. */
export const SESSION_COOKIE_NAME = "briefchain_session";

/** Backend API base URL. Defaults to http://localhost:8000 for local dev. */
export const API_BASE_URL =
  process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

/** Shape of the unified error returned by the BriefChain backend. */
export interface BriefChainError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

/** Parse a backend error response into a user-friendly message and optional code. */
export async function parseBackendError(response: Response): Promise<{ message: string; code?: string }> {
  try {
    const data = (await response.json()) as { error?: BriefChainError & { code?: string } };
    if (data.error?.message) {
      return { message: data.error.message, code: data.error.code };
    }
  } catch {
    // fall through to default message
  }
  return { message: `请求失败（${response.status}）` };
}

/** Client-side fetch helper that targets the internal Next.js API routes. */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<{ ok: true; data: T } | { ok: false; message: string; code?: string }> {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const { message, code } = await parseBackendError(response);
    return { ok: false, message, code };
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return { ok: true, data: undefined as T };
  }

  const data = (await response.json()) as T;
  return { ok: true, data };
}

/** Validate an email address with a simple regex. */
export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/** Validate that a value is non-empty after trimming. */
export function isNonEmpty(value: string): boolean {
  return value.trim().length > 0;
}

/** Minimum password length accepted by the frontend. */
export const MIN_PASSWORD_LENGTH = 6;
