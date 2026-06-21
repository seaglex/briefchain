import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { SESSION_COOKIE_NAME } from "./lib/auth";

const PUBLIC_PATHS = ["/login", "/register"];
const EXCLUDED_PATH_PREFIXES = [
  "/api/auth/",
  "/_next/",
  "/favicon.ico",
  "/next.svg",
  "/vercel.svg",
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Never guard internal/auth/static paths.
  if (EXCLUDED_PATH_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return NextResponse.next();
  }

  const hasSession = request.cookies.has(SESSION_COOKIE_NAME);

  // Authenticated users should not see login/register pages.
  if (hasSession && PUBLIC_PATHS.includes(pathname)) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  // Unauthenticated users can only access public pages.
  if (!hasSession && !PUBLIC_PATHS.includes(pathname)) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|.*\\..*$).*)"],
};
