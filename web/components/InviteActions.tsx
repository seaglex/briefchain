"use client";

import { useState } from "react";
import type { BriefDetail } from "@/components/BriefDetail";
import {
  acceptInvite,
  blockInvite,
  delegateInvite,
  openInvite,
  processInvite,
  rejectInvite,
  submitInvite,
} from "@/lib/invites";

interface InviteActionsProps {
  token: string;
  brief: BriefDetail;
  onActionComplete: () => void;
}

export default function InviteActions({ token, brief, onActionComplete }: InviteActionsProps) {
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionReason, setActionReason] = useState("");
  const [actionMode, setActionMode] = useState<
    "reject" | "submit" | "block" | "open" | "delegate" | "process" | null
  >(null);

  const reset = () => {
    setActionMode(null);
    setActionReason("");
    setActionError(null);
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
    onActionComplete();
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
    reset();
    onActionComplete();
  };

  const handleBlock = async () => {
    if (!actionReason.trim()) {
      setActionError("请填写阻塞原因");
      return;
    }
    setActionLoading(true);
    setActionError(null);
    const result = await blockInvite(token, { content: actionReason.trim() });
    setActionLoading(false);
    if (!result.ok) {
      setActionError(result.message);
      return;
    }
    reset();
    onActionComplete();
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
    reset();
    onActionComplete();
  };

  const handleOpen = async () => {
    if (!actionReason.trim()) {
      setActionError("请填写重新打开原因");
      return;
    }
    setActionLoading(true);
    setActionError(null);
    const result = await openInvite(token, { content: actionReason.trim() });
    setActionLoading(false);
    if (!result.ok) {
      setActionError(result.message);
      return;
    }
    reset();
    onActionComplete();
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
    reset();
    onActionComplete();
  };

  const handleProcess = async () => {
    setActionLoading(true);
    setActionError(null);
    const result = await processInvite(token, { content: actionReason.trim() || undefined });
    setActionLoading(false);
    if (!result.ok) {
      setActionError(result.message);
      return;
    }
    reset();
    onActionComplete();
  };

  if (brief.upstream_state === "sent") {
    return (
      <>
        {actionError && <div className="error-message mb-12">{actionError}</div>}
        <div className="flex gap-8 flex-wrap">
          <button className="btn btn-sm btn-primary" onClick={handleAccept} disabled={actionLoading}>
            {actionLoading ? "处理中..." : "接受"}
          </button>
          <button
            className="btn btn-sm btn-danger"
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
              <button className="btn" onClick={reset} disabled={actionLoading}>
                取消
              </button>
              <button className="btn btn-danger" onClick={handleReject} disabled={actionLoading}>
                {actionLoading ? "提交中..." : "确认拒绝"}
              </button>
            </div>
          </div>
        )}
      </>
    );
  }

  if (brief.upstream_state === "in_process") {
    const downstream = brief.downstream_state;
    return (
      <>
        {actionError && <div className="error-message mb-12">{actionError}</div>}
        <div className="flex gap-8 flex-wrap">
          <button
            className="btn btn-sm"
            onClick={() => setActionMode("process")}
            disabled={actionLoading}
          >
            进度更新
          </button>
          {downstream !== "submitted" && (
            <button
              className="btn btn-sm btn-primary"
              onClick={() => setActionMode("submit")}
              disabled={actionLoading}
            >
              提交完成
            </button>
          )}
          {(downstream === "submitted" || downstream === "delegated" || downstream === "blocked") && (
            <button
              className="btn btn-sm"
              onClick={() => setActionMode("open")}
              disabled={actionLoading}
            >
              重新打开
            </button>
          )}
          <button
            className="btn btn-sm"
            onClick={() => setActionMode("delegate")}
            disabled={actionLoading}
          >
            委托
          </button>
          <button
            className="btn btn-sm btn-danger"
            onClick={() => setActionMode("block")}
            disabled={actionLoading}
          >
            阻塞
          </button>
        </div>
        {actionMode === "process" && (
          <div className="mt-12">
            <div className="form-group">
              <label className="form-label">进度说明（可选）</label>
              <textarea
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                rows={4}
                placeholder="填写最新进度..."
              />
            </div>
            <div className="flex gap-8">
              <button className="btn" onClick={reset} disabled={actionLoading}>
                取消
              </button>
              <button className="btn btn-primary" onClick={handleProcess} disabled={actionLoading}>
                {actionLoading ? "提交中..." : "确认更新"}
              </button>
            </div>
          </div>
        )}
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
              <button className="btn" onClick={reset} disabled={actionLoading}>
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
              <button className="btn" onClick={reset} disabled={actionLoading}>
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
              <button className="btn" onClick={reset} disabled={actionLoading}>
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
              <button className="btn" onClick={reset} disabled={actionLoading}>
                取消
              </button>
              <button className="btn btn-danger" onClick={handleBlock} disabled={actionLoading}>
                {actionLoading ? "提交中..." : "确认阻塞"}
              </button>
            </div>
          </div>
        )}
      </>
    );
  }

  return null;
}
