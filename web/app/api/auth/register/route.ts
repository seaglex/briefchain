import { NextRequest, NextResponse } from "next/server";
import { API_BASE_URL, SESSION_COOKIE_NAME, parseBackendError } from "@/lib/auth";

export async function POST(request: NextRequest) {
  const body = (await request.json()) as {
    name?: string;
    email?: string;
    phone?: string;
    password?: string;
  };

  const name = body.name?.trim() || "";
  const email = body.email?.trim() || undefined;
  const phone = body.phone?.trim() || undefined;
  const password = body.password || "";

  if (!name || !password) {
    return NextResponse.json(
      {
        error: {
          code: "VALIDATION_ERROR",
          message: "姓名和密码不能为空",
        },
      },
      { status: 422 }
    );
  }

  if (!email && !phone) {
    return NextResponse.json(
      {
        error: {
          code: "VALIDATION_ERROR",
          message: "邮箱和手机号至少填写一项",
        },
      },
      { status: 422 }
    );
  }

  const backendResponse = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, phone, password }),
  });

  if (!backendResponse.ok) {
    const message = await parseBackendError(backendResponse);
    return NextResponse.json(
      { error: { code: "REGISTER_FAILED", message } },
      { status: backendResponse.status }
    );
  }

  const data = (await backendResponse.json()) as { token: string; user: unknown };

  const response = NextResponse.json({ user: data.user });
  response.cookies.set(SESSION_COOKIE_NAME, data.token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 7, // 7 days
  });

  return response;
}
