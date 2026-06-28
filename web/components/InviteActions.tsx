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
    "reject" | "submit" | "block" | "open" | "delegate" | "sync" | null
  >(null);

  const reset = () => {
    setActionMode(null);
    setActionReason("");
    setActionError(null);
  };

  const handleAction = async (
    fn: () => Promise<{ ok: boolean; message?: string } | { ok: boolean; data?: unknown; message?: string }>,
    onSuccess?: () => void
  ) => {
    setActionLoading(true);
    setActionError(null);
    const result = await fn();
    setActionLoading(false);
    if (!result.ok) {
      setActionError(result.message || "操作失败");
      return;
    }
    if (onSuccess) onSuccess();
  };

  const handleAccept = () => {
    handleAction(() => acceptInvite(token), onActionComplete);
  };

  const handleReject = () => {
    if (!actionReason.trim()) {
      setActionError("请填写拒绝原因");
      return;
    }
    handleAction(
      () => rejectInvite(token, { reason: actionReason.trim() }),
      () => {
        reset();
        onActionComplete();
      }
    );
  };

  const handleBlock = () => {
    if (!actionReason.trim()) {
      setActionError("请填写阻塞原因");
      return;
    }
    handleAction(
      () => blockInvite(token, { content: actionReason.trim() }),
      () => {
        reset();
        onActionComplete();
      }
    );
  };

  const handleSubmit = () => {
    if (!actionReason.trim()) {
      setActionError("请填写完成说明");
      return;
    }
    handleAction(
      () => submitInvite(token, { content: actionReason.trim() }),
      () => {
        reset();
        onActionComplete();
      }
    );
  };

  const handleOpen = () => {
    if (!actionReason.trim()) {
      setActionError("请填写重新打开原因");
      return;
    }
    handleAction(
      () => openInvite(token, { content: actionReason.trim() }),
      () => {
        reset();
        onActionComplete();
      }
    );
  };

  const handleDelegate = () => {
    handleAction(
      () => delegateInvite(token, { content: actionReason.trim() || undefined }),
      () => {
        reset();
        onActionComplete();
      }
    );
  };

  const handleSync = () => {
    handleAction(
      () => processInvite(token, { content: actionReason.trim() || undefined }),
      () => {
        reset();
        onActionComplete();
      }
    );
  };

  const modalTitle = () => {
    switch (actionMode) {
      case "reject":
        return "拒绝 Brief";
      case "submit":
        return "提交结果";
      case "open":
        return "待处理";
      case "delegate":
        return "委托说明";
      case "block":
        return "标记阻塞";
      case "sync":
        return "同步进度";
      default:
        return "";
    }
  };

  const renderModal = () => {
    if (!actionMode) return null;

    const isRequired = actionMode !== "delegate" && actionMode !== "sync";
    const labelMap: Record<Exclude<typeof actionMode, null>, string> = {
      reject: "拒绝原因",
      submit: "完成说明",
      open: "待处理说明",
      delegate: "委托说明（可选）",
      block: "阻塞原因",
      sync: "同步说明（可选）",
    };

    const confirmMap: Record<Exclude<typeof actionMode, null>, { label: string; variant: string; handler: () => void }> = {
      reject: { label: "确认拒绝", variant: "btn-danger", handler: handleReject },
      submit: { label: "确认提交", variant: "btn-primary", handler: handleSubmit },
      open: { label: "确认", variant: "btn-primary", handler: handleOpen },
      delegate: { label: "确认委托", variant: "btn-primary", handler: handleDelegate },
      block: { label: "确认阻塞", variant: "btn-danger", handler: handleBlock },
      sync: { label: "确认同步", variant: "btn-primary", handler: handleSync },
    };

    const { label, variant, handler } = confirmMap[actionMode];

    return (
      <div className="modal-overlay" onClick={reset}>
        <div className="modal-card" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>{modalTitle()}</h3>
            <button className="btn btn-sm" onClick={reset}>关闭</button>
          </div>
          <div className="modal-body">
            {actionError && <div className="error-message mb-12">{actionError}</div>}
            <div className="form-group">
              <label className="form-label">
                {labelMap[actionMode]}
                {isRequired && " *"}
              </label>
              <textarea
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                rows={5}
                placeholder={`请填写${labelMap[actionMode].replace("（可选）", "")}...`}
              />
            </div>
          </div>
          <div className="modal-footer">
            <button className="btn" onClick={reset} disabled={actionLoading}>取消</button>
            <button className={`btn ${variant}`} onClick={handler} disabled={actionLoading}>
              {actionLoading ? "提交中..." : label}
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderDownstreamActions = () => {
    const upstream = brief.upstream_state;

    if (upstream === "sent") {
      return (
        <div className="detail-header-actions-group">
          <button
            className="btn btn-sm btn-primary"
            onClick={handleAccept}
            disabled={actionLoading}
          >
            接受
          </button>
          <button
            className="btn btn-sm btn-danger"
            onClick={() => setActionMode("reject")}
            disabled={actionLoading}
          >
            拒绝
          </button>
        </div>
      );
    }

    if (upstream === "in_process" || upstream === "suspended") {
      const downstream = brief.downstream_state;
      return (
        <div className="detail-header-actions-group">
          <button
            className="btn btn-sm"
            onClick={() => setActionMode("sync")}
            disabled={actionLoading}
          >
            同步进度
          </button>
          {downstream !== "opened" && (
            <button
              className="btn btn-sm"
              onClick={() => setActionMode("open")}
              disabled={actionLoading}
            >
              待处理
            </button>
          )}
          {downstream !== "delegated" && (
            <button
              className="btn btn-sm"
              onClick={() => setActionMode("delegate")}
              disabled={actionLoading}
            >
              已安排
            </button>
          )}
          {downstream !== "blocked" && (
            <button
              className="btn btn-sm btn-danger"
              onClick={() => setActionMode("block")}
              disabled={actionLoading}
            >
              遇阻
            </button>
          )}
          {downstream !== "submitted" && (
            <button
              className="btn btn-sm btn-primary"
              onClick={() => setActionMode("submit")}
              disabled={actionLoading}
            >
              提交结果
            </button>
          )}
        </div>
      );
    }

    // cancelled / done / editing -> no downstream actions
    return null;
  };

  // Invited users only have downstream permissions; there is no upstream group.
  // We keep the same wrapper structure as BriefActions for consistent layout.
  return (
    <>
      {renderDownstreamActions()}
      {renderModal()}
    </>
  );
}
