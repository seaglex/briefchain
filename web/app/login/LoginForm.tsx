"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch, isNonEmpty } from "@/lib/auth";

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const inviteToken = searchParams.get("invite_token");

  const [emailOrPhone, setEmailOrPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const validate = (): boolean => {
    if (!isNonEmpty(emailOrPhone) || !isNonEmpty(password)) {
      setError("邮箱/手机号和密码不能为空");
      return false;
    }
    setError(null);
    return true;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!validate()) return;

    setLoading(true);
    const body: Record<string, string> = {
      email_or_phone: emailOrPhone,
      password,
    };
    if (inviteToken) body.invite_token = inviteToken;

    const result = await apiFetch<{ user: unknown }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    });
    setLoading(false);

    if (!result.ok) {
      setError(result.message);
      return;
    }

    router.replace("/");
  };

  const registerHref = inviteToken
    ? `/register?invite_token=${encodeURIComponent(inviteToken)}`
    : "/register";

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <h1 style={{ marginTop: 8 }}>BriefChain</h1>
          <p className="text-2" style={{ fontSize: 12, marginTop: 4 }}>
            AI-reviewed briefs for smoother handoffs
          </p>
        </div>

        <div className="card">
          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email_or_phone" className="form-label">
                邮箱或手机号
              </label>
              <input
                id="email_or_phone"
                type="text"
                placeholder="user@example.com 或 +86 138 0000 0000"
                value={emailOrPhone}
                onChange={(e) => setEmailOrPhone(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password" className="form-label">
                密码
              </label>
              <input
                id="password"
                type="password"
                placeholder="输入密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: "100%", marginTop: 8 }}
              disabled={loading}
            >
              {loading ? "登录中..." : "登录"}
            </button>
          </form>

          <p style={{ textAlign: "center", marginTop: 16, fontSize: 12, color: "var(--c-text-3)" }}>
            还没有账号？{" "}
            <Link href={registerHref} style={{ color: "var(--c-primary)" }}>
              注册
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
