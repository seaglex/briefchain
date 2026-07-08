import { NextRequest, NextResponse } from "next/server";
import { API_BASE_URL, SESSION_COOKIE_NAME, parseBackendError } from "@/lib/auth";
import { getSessionCookieOptions } from "@/lib/server-auth";

export async function POST(request: NextRequest) {
  const body = (await request.json()) as {
    email_or_phone?: string;
    password?: string;
    invite_token?: string;
  };

  const emailOrPhone = body.email_or_phone?.trim() || "";
  const password = body.password || "";
  const inviteToken = body.invite_token?.trim();

  if (!emailOrPhone || !password) {
    return NextResponse.json(
      {
        error: {
          code: "VALIDATION_ERROR",
          message: "邮箱/手机号和密码不能为空",
        },
      },
      { status: 422 }
    );
  }

  // The backend LoginRequest expects separate `email` and `phone` fields.
  // We detect the input type here to stay compatible with the existing API.
  const isEmail = emailOrPhone.includes("@");
  const backendBody: Record<string, string | undefined> = isEmail
    ? { email: emailOrPhone, password }
    : { phone: emailOrPhone, password };
  if (inviteToken) backendBody.invite_token = inviteToken;

  const backendResponse = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(backendBody),
  });

  if (!backendResponse.ok) {
    const { message } = await parseBackendError(backendResponse);
    return NextResponse.json(
      { error: { code: "AUTH_FAILED", message } },
      { status: backendResponse.status }
    );
  }

  const data = (await backendResponse.json()) as { token: string; user: unknown };

  const response = NextResponse.json({ user: data.user });
  response.cookies.set(SESSION_COOKIE_NAME, data.token, getSessionCookieOptions(request));

  return response;
}
