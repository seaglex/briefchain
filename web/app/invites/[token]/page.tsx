"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import BriefDetailView, {
  BriefDetail,
  Feedback,
  Transfer,
} from "@/components/BriefDetail";
import InviteActions from "@/components/InviteActions";
import {
  getInvite,
  getInviteFeedbacks,
  getInviteTransfers,
} from "@/lib/invites";

interface ApiError {
  code: string;
  message: string;
}

function InviteHeader({ invite }: { invite: { name: string; from_user: { id: string; name: string } } }) {
  return (
    <header style={{ borderBottom: "1px solid var(--c-border)" }}>
      <div
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          padding: "16px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div className="flex items-center gap-12">
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: "var(--c-primary)",
              color: "#fff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
            }}
          >
            B
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 18 }}>BriefChain</div>
            <div className="text-2" style={{ fontSize: 12 }}>
              AI-reviewed briefs for smoother handoffs
            </div>
          </div>
        </div>
      </div>
      <div
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          padding: "8px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-end",
          gap: 16,
          fontSize: 14,
        }}
      >
        <span className="text-2">
          {invite.name}，欢迎加入 BriefChain，轻松管理任务
        </span>
        <Link href="/login" className="text-link">
          登录
        </Link>
        <Link href="/register" className="text-link">
          注册
        </Link>
      </div>
    </header>
  );
}

function ErrorView({ error, token }: { error: ApiError; token: string }) {
  const isExpired = error.code === "INVITE_EXPIRED";
  const isInvalidated = error.code === "INVITE_INVALIDATED";

  return (
    <div className="card" style={{ maxWidth: 560, margin: "80px auto", textAlign: "center" }}>
      <h2 className="mb-12">
        {isExpired ? "邀请链接已过期" : isInvalidated ? "邀请链接已失效" : "邀请链接无效"}
      </h2>
      <p className="text-2 mb-16">
        {isExpired
          ? "该邀请已超过接受截止时间，请联系发送方重新发送。"
          : isInvalidated
            ? "此邀请已失效，请登录您的账号继续操作。"
            : error.message || "无法加载邀请信息，请检查链接是否正确。"}
      </p>
      <div className="flex gap-8 justify-center">
        <Link href="/login" className="btn btn-primary">
          登录
        </Link>
        <Link href="/register" className="btn">
          注册
        </Link>
      </div>
    </div>
  );
}

export default function InvitePage() {
  const params = useParams();
  const token = params.token as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [invite, setInvite] = useState<{
    name: string;
    from_user: { id: string; name: string };
    accept_deadline: string;
    complete_deadline: string;
  } | null>(null);
  const [brief, setBrief] = useState<BriefDetail | null>(null);
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);

  useEffect(() => {
    if (!token) return;

    async function load() {
      setLoading(true);
      setError(null);

      const [inviteResult, transfersResult, feedbacksResult] = await Promise.all([
        getInvite(token),
        getInviteTransfers(token),
        getInviteFeedbacks(token),
      ]);

      setLoading(false);

      if (!inviteResult.ok) {
        setError({ code: inviteResult.code || "UNKNOWN", message: inviteResult.message });
        return;
      }

      setInvite(inviteResult.data.invite);
      setBrief(inviteResult.data.brief);
      setTransfers(transfersResult.ok ? transfersResult.data : []);
      setFeedbacks(feedbacksResult.ok ? feedbacksResult.data : []);
    }

    load();
  }, [token]);

  const reload = async () => {
    const [inviteResult, transfersResult, feedbacksResult] = await Promise.all([
      getInvite(token),
      getInviteTransfers(token),
      getInviteFeedbacks(token),
    ]);

    if (inviteResult.ok) {
      setBrief(inviteResult.data.brief);
      setInvite(inviteResult.data.invite);
    }
    setTransfers(transfersResult.ok ? transfersResult.data : []);
    setFeedbacks(feedbacksResult.ok ? feedbacksResult.data : []);
  };

  if (loading) {
    return (
      <div className="min-h-screen">
        <div className="text-center py-24">加载中...</div>
      </div>
    );
  }

  if (error || !invite || !brief) {
    return (
      <div className="min-h-screen">
        <ErrorView error={error || { code: "UNKNOWN", message: "加载失败" }} token={token} />
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: "var(--c-bg)" }}>
      <InviteHeader invite={invite} />
      <div className="app" style={{ height: "auto", minHeight: "calc(100vh - 80px)" }}>
        <div className="main">
          <div className="content">
            <BriefDetailView
              brief={brief}
              transfers={transfers}
              feedbacks={feedbacks}
              readOnly
              actions={
                <InviteActions token={token} brief={brief} onActionComplete={reload} />
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
}
