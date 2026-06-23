"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, isNonEmpty } from "@/lib/auth";
import { sendBrief } from "@/lib/invites";
import UserSelector from "@/components/UserSelector";

interface BriefActionsProps {
  briefId: string;
  status: string;
  title: string;
  content: string;
  priority: string;
  estimatedManDays: number | null;
  isCreator: boolean;
  isAssignee: boolean;
}

export default function BriefActions({
  briefId,
  status,
  title,
  content,
  priority,
  estimatedManDays,
  isCreator,
  isAssignee,
}: BriefActionsProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Edit state
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(title);
  const [editContent, setEditContent] = useState(content);
  const [editPriority, setEditPriority] = useState(priority);
  const [editEstimated, setEditEstimated] = useState(
    estimatedManDays?.toString() || ""
  );

  // Modal state
  const [modal, setModal] = useState<
    | null
    | "send"
    | "reject"
    | "complete"
    | "blocked"
  >(null);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [reason, setReason] = useState("");

  // Send mode state
  const [sendMode, setSendMode] = useState<"registered" | "temporary">("registered");
  const [recipientName, setRecipientName] = useState("");
  const [recipientEmailOrPhone, setRecipientEmailOrPhone] = useState("");
  const [inviteResult, setInviteResult] = useState<{
    invite_url: string;
    accept_deadline: string;
    complete_deadline: string;
  } | null>(null);
  const [copied, setCopied] = useState(false);

  const handleAction = async (
    path: string,
    body?: object,
    onSuccess?: () => void
  ) => {
    setLoading(true);
    setError(null);
    const result = await apiFetch(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
    setLoading(false);

    if (!result.ok) {
      setError(result.message);
      return;
    }

    if (onSuccess) onSuccess();
    router.refresh();
  };

  const handleEdit = async () => {
    if (!isNonEmpty(editTitle) || !isNonEmpty(editContent)) {
      setError("标题和内容不能为空");
      return;
    }

    setLoading(true);
    setError(null);
    const result = await apiFetch(`/api/briefs/${briefId}`, {
      method: "PATCH",
      body: JSON.stringify({
        title: editTitle.trim(),
        content: editContent.trim(),
        priority: editPriority,
        estimated_man_days: editEstimated ? parseFloat(editEstimated) : null,
        revision_reason: "更新内容",
      }),
    });
    setLoading(false);

    if (!result.ok) {
      setError(result.message);
      return;
    }

    setIsEditing(false);
    router.refresh();
  };

  const handleSend = async () => {
    if (sendMode === "registered") {
      if (!selectedUserId) {
        setError("请选择 downstream 用户");
        return;
      }
      await handleAction(`/api/briefs/${briefId}/send`, {
        assigned_to: selectedUserId,
        note: note.trim() || undefined,
      });
      resetSendModal();
      return;
    }

    if (!isNonEmpty(recipientName)) {
      setError("请填写接收人姓名");
      return;
    }

    setLoading(true);
    setError(null);
    const trimmedContact = recipientEmailOrPhone.trim();
    const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedContact);
    const result = await sendBrief(briefId, {
      is_temporary_user: true,
      recipient_name: recipientName.trim(),
      recipient_email: isEmail ? trimmedContact : undefined,
      recipient_phone: isEmail ? undefined : trimmedContact || undefined,
      note: note.trim() || undefined,
    });
    setLoading(false);

    if (!result.ok) {
      setError(result.message);
      return;
    }

    if (result.data.invite) {
      setInviteResult(result.data.invite);
    } else {
      resetSendModal();
      router.refresh();
    }
  };

  const handleReject = async () => {
    if (!isNonEmpty(reason)) {
      setError("请填写拒绝原因");
      return;
    }
    await handleAction(`/api/briefs/${briefId}/reject`, { reason: reason.trim() });
    setModal(null);
    setReason("");
  };

  const handleComplete = async () => {
    if (!isNonEmpty(reason)) {
      setError("请填写完成说明");
      return;
    }
    // First create completion feedback, then mark complete
    const feedbackResult = await apiFetch(`/api/briefs/${briefId}/feedbacks`, {
      method: "POST",
      body: JSON.stringify({
        type: "completion",
        content: reason.trim(),
        attachments: [],
      }),
    });
    if (!feedbackResult.ok) {
      setError(feedbackResult.message);
      return;
    }
    await handleAction(`/api/briefs/${briefId}/complete`);
    setModal(null);
    setReason("");
  };

  const handleBlocked = async () => {
    if (!isNonEmpty(reason)) {
      setError("请填写阻塞原因");
      return;
    }
    await handleAction(`/api/briefs/${briefId}/feedbacks`, {
      type: "blocked",
      content: reason.trim(),
      attachments: [],
    });
    setModal(null);
    setReason("");
  };

  const closeModal = () => {
    setModal(null);
    setError(null);
    setSelectedUserId(null);
    setNote("");
    setReason("");
    resetSendModal();
  };

  const resetSendModal = () => {
    setSendMode("registered");
    setRecipientName("");
    setRecipientEmailOrPhone("");
    setInviteResult(null);
    setCopied(false);
  };

  const handleCopyInviteLink = async () => {
    if (!inviteResult) return;
    const url = `${window.location.origin}${inviteResult.invite_url}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  const renderModal = () => {
    if (!modal) return null;

    return (
      <div className="modal-overlay" onClick={closeModal}>
        <div className="modal-card" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>
              {modal === "send"
                ? "发送给 downstream"
                : modal === "reject"
                  ? "拒绝 Brief"
                  : modal === "complete"
                    ? "标记完成"
                    : "标记阻塞"}
            </h3>
            <button className="btn btn-sm" onClick={closeModal}>关闭</button>
          </div>

          <div className="modal-body">
            {error && <div className="error-message mb-12">{error}</div>}

            {modal === "send" && !inviteResult && (
              <>
                <div className="form-group">
                  <label className="form-label">发送方式</label>
                  <div className="flex gap-8">
                    <button
                      type="button"
                      className={`btn btn-sm ${sendMode === "registered" ? "btn-primary" : ""}`}
                      onClick={() => setSendMode("registered")}
                    >
                      已注册用户
                    </button>
                    <button
                      type="button"
                      className={`btn btn-sm ${sendMode === "temporary" ? "btn-primary" : ""}`}
                      onClick={() => setSendMode("temporary")}
                    >
                      临时用户
                    </button>
                  </div>
                </div>

                {sendMode === "registered" && (
                  <div className="form-group">
                    <label className="form-label">选择 downstream 用户</label>
                    <UserSelector
                      selectedUserId={selectedUserId}
                      onSelect={setSelectedUserId}
                    />
                  </div>
                )}

                {sendMode === "temporary" && (
                  <>
                    <div className="form-group">
                      <label className="form-label">接收人姓名 *</label>
                      <input
                        type="text"
                        value={recipientName}
                        onChange={(e) => setRecipientName(e.target.value)}
                        placeholder="例如：李四"
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">邮箱或手机号（可选）</label>
                      <input
                        type="text"
                        value={recipientEmailOrPhone}
                        onChange={(e) => setRecipientEmailOrPhone(e.target.value)}
                        placeholder="example@email.com 或 13800000000"
                      />
                    </div>
                  </>
                )}

                <div className="form-group">
                  <label className="form-label">备注（可选）</label>
                  <textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    rows={3}
                    placeholder="可选填写备注"
                  />
                </div>
              </>
            )}

            {modal === "send" && inviteResult && (
              <div className="form-group">
                <label className="form-label">邀请链接已生成</label>
                <div className="flex gap-8 items-start">
                  <input
                    type="text"
                    readOnly
                    value={`${typeof window !== "undefined" ? window.location.origin : ""}${inviteResult.invite_url}`}
                    style={{ flex: 1 }}
                  />
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleCopyInviteLink}
                  >
                    {copied ? "已复制" : "复制"}
                  </button>
                </div>
                <p className="text-3 mt-8" style={{ fontSize: 12 }}>
                  接受截止：{new Date(inviteResult.accept_deadline).toLocaleString("zh-CN")}
                </p>
              </div>
            )}

            {(modal === "reject" || modal === "complete" || modal === "blocked") && (
              <div className="form-group">
                <label className="form-label">
                  {modal === "reject"
                    ? "拒绝原因"
                    : modal === "complete"
                      ? "完成说明"
                      : "阻塞原因"}
                </label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={5}
                  placeholder="请填写说明..."
                />
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button className="btn" onClick={closeModal} disabled={loading}>
              {modal === "send" && inviteResult ? "关闭" : "取消"}
            </button>
            {!(modal === "send" && inviteResult) && (
              <button
                className="btn btn-primary"
                onClick={
                  modal === "send"
                    ? handleSend
                    : modal === "reject"
                      ? handleReject
                      : modal === "complete"
                        ? handleComplete
                        : handleBlocked
                }
                disabled={loading}
              >
                {loading ? "提交中..." : "确认"}
              </button>
            )}
            {modal === "send" && inviteResult && (
              <button
                className="btn btn-primary"
                onClick={() => {
                  closeModal();
                  router.refresh();
                }}
              >
                完成
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (isEditing) {
    return (
      <div className="card mb-16">
        {error && <div className="error-message mb-12">{error}</div>}
        <div className="form-group">
          <label className="form-label">标题</label>
          <input
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label className="form-label">内容</label>
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            rows={6}
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label className="form-label">优先级</label>
          <select
            value={editPriority}
            onChange={(e) => setEditPriority(e.target.value)}
            disabled={loading}
          >
            <option value="p0">P0</option>
            <option value="p1">P1</option>
            <option value="p2">P2</option>
            <option value="p3">P3</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">预估人天</label>
          <input
            type="number"
            min="0"
            step="0.5"
            value={editEstimated}
            onChange={(e) => setEditEstimated(e.target.value)}
            disabled={loading}
          />
        </div>
        <div className="flex gap-8">
          <button className="btn" onClick={() => setIsEditing(false)} disabled={loading}>
            取消
          </button>
          <button className="btn btn-primary" onClick={handleEdit} disabled={loading}>
            {loading ? "保存中..." : "保存"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="flex gap-8">
        {isCreator && status === "draft" && (
          <>
            <button className="btn btn-sm" onClick={() => setIsEditing(true)}>
              编辑
            </button>
            <button
              className="btn btn-sm btn-primary"
              onClick={() => handleAction(`/api/briefs/${briefId}/submit`)}
              disabled={loading}
            >
              提交审查
            </button>
          </>
        )}

        {isCreator && status === "reviewed" && (
          <button
            className="btn btn-sm btn-primary"
            onClick={() => setModal("send")}
            disabled={loading}
          >
            发送给 downstream
          </button>
        )}

        {isAssignee && status === "sent" && (
          <>
            <button
              className="btn btn-sm btn-primary"
              onClick={() => handleAction(`/api/briefs/${briefId}/accept`)}
              disabled={loading}
            >
              接受
            </button>
            <button
              className="btn btn-sm btn-danger"
              onClick={() => setModal("reject")}
              disabled={loading}
            >
              拒绝
            </button>
          </>
        )}

        {isAssignee && status === "accepted" && (
          <>
            <button
              className="btn btn-sm btn-primary"
              onClick={() => setModal("complete")}
              disabled={loading}
            >
              标记完成
            </button>
            <button
              className="btn btn-sm btn-danger"
              onClick={() => setModal("blocked")}
              disabled={loading}
            >
              标记阻塞
            </button>
          </>
        )}
      </div>
      {renderModal()}
    </>
  );
}
