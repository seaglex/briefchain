"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import BriefDetailView, {
  BriefDetail,
  Feedback,
  Transfer,
} from "@/components/BriefDetail";
import {
  acceptInvite,
  blockInvite,
  delegateInvite,
  getInvite,
  getInviteFeedbacks,
  getInviteTransfers,
  openInvite,
  rejectInvite,
  submitInvite,
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
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionReason, setActionReason] = useState("");
  const [actionMode, setActionMode] = useState<"reject" | "submit" | "block" | "open" | "delegate" | null>(null);

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

  const handleAccept = async () => {
    setActionLoading(true);
    setActionError(null);
    const result = await acceptInvite(token);
    setActionLoading(false);
    if (!result.ok) {
      setActionError(result.message);
      return;
    }
    await reload();
  };

  const handleReject = async () => {
    if (!actionReason.trim()) {
      setActionError("请填写拒绝原因");
      return;
    }
    setActionLoading(true);
    setActionError(null);
    const result = await rejectInvite(token, { reason: actionReason.trim() });
    setActionLoading(false);
    if (!result.ok) {
      setActionError(result.message);
      return;
    }
    setActionMode(null);
    setActionReason("");
    await reload();
  };

  const handleBlock = async () => {
    if (!actionReason.trim()) {
      setActionError("请填写阻塞原因");
      return;
    }
    setActionLoading(true);
    setActionError(null);
    const result = await blockInvite(token, { reason: actionReason.trim() });
    setActionLoading(false);
    if (!result.ok) {
      setActionError(result.message);
      return;
    }
    setActionMode(null);
    setActionReason("");
    await reload();
  };

  const handleSubmit = async () => {
    if (!actionReason.trim()) {
      setActionError("请填写完成说明");
      return;
    }
    setActionLoading(true);
    setActionError(null);
    const result = await submitInvite(token, { content: actionReason.trim() });
    setActionLoading(false);
    if (!result.ok) {
      setActionError(result.message);
      return;
    }
    setActionMode(null);
    setActionReason("");
    await reload();
  };

  const handleOpen = async () => {
    if (!actionReason.trim()) {
      setActionError("请填写重新打开原因");
      return;
    }
    setActionLoading(true);
    setActionError(null);
    const result = await openInvite(token, { reason: actionReason.trim() });
    setActionLoading(false);
    if (!result.ok) {
      setActionError(result.message);
      return;
    }
    setActionMode(null);
    setActionReason("");
    await reload();
  };

  const handleDelegate = async () => {
    setActionLoading(true);
    setActionError(null);
    const result = await delegateInvite(token, { content: actionReason.trim() || undefined });
    setActionLoading(false);
    if (!result.ok) {
      setActionError(result.message);
      return;
    }
    setActionMode(null);
    setActionReason("");
    await reload();
  };

  const renderActionControls = () => {
    if (!brief) return null;

    if (brief.upstream_state === "sent") {
      return (
        <div className="card mt-16">
          {actionError && <div className="error-message mb-12">{actionError}</div>}
          <div className="flex gap-8">
            <button
              className="btn btn-primary"
              onClick={handleAccept}
              disabled={actionLoading}
            >
              {actionLoading ? "处理中..." : "接受"}
            </button>
            <button
              className="btn btn-danger"
              onClick={() => setActionMode("reject")}
              disabled={actionLoading}
            >
              拒绝
            </button>
          </div>
          {actionMode === "reject" && (
            <div className="mt-12">
              <div className="form-group">
                <label className="form-label">拒绝原因</label>
                <textarea
                  value={actionReason}
                  onChange={(e) => setActionReason(e.target.value)}
                  rows={4}
                  placeholder="请填写拒绝原因"
                />
              </div>
              <div className="flex gap-8">
                <button className="btn" onClick={() => { setActionMode(null); setActionReason(""); setActionError(null); }} disabled={actionLoading}>
                  取消
                </button>
                <button className="btn btn-danger" onClick={handleReject} disabled={actionLoading}>
                  {actionLoading ? "提交中..." : "确认拒绝"}
                </button>
              </div>
            </div>
          )}
        </div>
      );
    }

    if (brief.upstream_state === "in_process") {
      const downstream = brief.downstream_state;
      return (
        <div className="card mt-16">
          {actionError && <div className="error-message mb-12">{actionError}</div>}
          <div className="flex gap-8 flex-wrap">
            {downstream !== "submitted" && (
              <button
                className="btn btn-primary"
                onClick={() => setActionMode("submit")}
                disabled={actionLoading}
              >
                提交完成
              </button>
            )}
            {(downstream === "submitted" || downstream === "delegated" || downstream === "blocked") && (
              <button
                className="btn"
                onClick={() => setActionMode("open")}
                disabled={actionLoading}
              >
                重新打开
              </button>
            )}
            <button
              className="btn"
              onClick={() => setActionMode("delegate")}
              disabled={actionLoading}
            >
              委托
            </button>
            <button
              className="btn btn-danger"
              onClick={() => setActionMode("block")}
              disabled={actionLoading}
            >
              阻塞
            </button>
          </div>
          {actionMode === "submit" && (
            <div className="mt-12">
              <div className="form-group">
                <label className="form-label">完成说明</label>
                <textarea
                  value={actionReason}
                  onChange={(e) => setActionReason(e.target.value)}
                  rows={4}
                  placeholder="请填写完成说明"
                />
              </div>
              <div className="flex gap-8">
                <button className="btn" onClick={() => { setActionMode(null); setActionReason(""); setActionError(null); }} disabled={actionLoading}>
                  取消
                </button>
                <button className="btn btn-primary" onClick={handleSubmit} disabled={actionLoading}>
                  {actionLoading ? "提交中..." : "确认完成"}
                </button>
              </div>
            </div>
          )}
          {actionMode === "open" && (
            <div className="mt-12">
              <div className="form-group">
                <label className="form-label">重新打开原因</label>
                <textarea
                  value={actionReason}
                  onChange={(e) => setActionReason(e.target.value)}
                  rows={4}
                  placeholder="请填写重新打开原因"
                />
              </div>
              <div className="flex gap-8">
                <button className="btn" onClick={() => { setActionMode(null); setActionReason(""); setActionError(null); }} disabled={actionLoading}>
                  取消
                </button>
                <button className="btn btn-primary" onClick={handleOpen} disabled={actionLoading}>
                  {actionLoading ? "提交中..." : "确认打开"}
                </button>
              </div>
            </div>
          )}
          {actionMode === "delegate" && (
            <div className="mt-12">
              <div className="form-group">
                <label className="form-label">委托说明（可选）</label>
                <textarea
                  value={actionReason}
                  onChange={(e) => setActionReason(e.target.value)}
                  rows={4}
                  placeholder="请填写委托说明"
                />
              </div>
              <div className="flex gap-8">
                <button className="btn" onClick={() => { setActionMode(null); setActionReason(""); setActionError(null); }} disabled={actionLoading}>
                  取消
                </button>
                <button className="btn btn-primary" onClick={handleDelegate} disabled={actionLoading}>
                  {actionLoading ? "提交中..." : "确认委托"}
                </button>
              </div>
            </div>
          )}
          {actionMode === "block" && (
            <div className="mt-12">
              <div className="form-group">
                <label className="form-label">阻塞原因</label>
                <textarea
                  value={actionReason}
                  onChange={(e) => setActionReason(e.target.value)}
                  rows={4}
                  placeholder="请填写阻塞原因"
                />
              </div>
              <div className="flex gap-8">
                <button className="btn" onClick={() => { setActionMode(null); setActionReason(""); setActionError(null); }} disabled={actionLoading}>
                  取消
                </button>
                <button className="btn btn-danger" onClick={handleBlock} disabled={actionLoading}>
                  {actionLoading ? "提交中..." : "确认阻塞"}
                </button>
              </div>
            </div>
          )}
        </div>
      );
    }

    return null;
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
            <BriefDetailView brief={brief} transfers={transfers} feedbacks={feedbacks} readOnly />
            {renderActionControls()}
          </div>
        </div>
      </div>
    </div>
  );
}
