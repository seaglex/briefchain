"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  apiFetch,
  isNonEmpty,
  isValidEmail,
  MIN_PASSWORD_LENGTH,
} from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const inviteToken = searchParams.get("invite_token");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const validate = (): boolean => {
    if (!isNonEmpty(name)) {
      setError("姓名不能为空");
      return false;
    }

    const emailValue = email.trim();
    const phoneValue = phone.trim();

    if (!emailValue && !phoneValue) {
      setError("邮箱和手机号至少填写一项");
      return false;
    }

    if (emailValue && !isValidEmail(emailValue)) {
      setError("邮箱格式不正确");
      return false;
    }

    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(`密码长度不能少于 ${MIN_PASSWORD_LENGTH} 位`);
      return false;
    }

    setError(null);
    return true;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!validate()) return;

    setLoading(true);
    const body: Record<string, string | undefined> = {
      name: name.trim(),
      email: email.trim() || undefined,
      phone: phone.trim() || undefined,
      password,
    };
    if (inviteToken) body.invite_token = inviteToken;

    const result = await apiFetch<{ user: unknown }>("/api/auth/register", {
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

  const loginHref = inviteToken
    ? `/login?invite_token=${encodeURIComponent(inviteToken)}`
    : "/login";

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
              <label htmlFor="name" className="form-label">
                姓名
              </label>
              <input
                id="name"
                type="text"
                placeholder="请输入姓名"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="email" className="form-label">
                邮箱（可选）
              </label>
              <input
                id="email"
                type="email"
                placeholder="user@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="phone" className="form-label">
                手机号（可选）
              </label>
              <input
                id="phone"
                type="tel"
                placeholder="+86 138 0000 0000"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
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
                placeholder="设置密码（不少于 6 位）"
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
              {loading ? "注册中..." : "注册"}
            </button>
          </form>

          <p style={{ textAlign: "center", marginTop: 16, fontSize: 12, color: "var(--c-text-3)" }}>
            已有账号？{" "}
            <Link href={loginHref} style={{ color: "var(--c-primary)" }}>
              登录
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
