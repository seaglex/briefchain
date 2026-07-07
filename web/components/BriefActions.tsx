"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, isNonEmpty } from "@/lib/auth";
import { isoToLocalDateTime, localDateTimeToISO } from "@/lib/date";
import { sendBrief } from "@/lib/invites";
import { BRIEF_TYPE_LABELS, type BriefType } from "@/lib/brief-types";
import UserSelector from "@/components/UserSelector";

interface BriefActionsProps {
  briefId: string;
  type: BriefType;
  upstreamState: string;
  downstreamState: string | null;
  title: string;
  content: string;
  priority: string;
  estimatedManDays: number | null;
  expectedCompletionAt: string | null;
  currentVersionStatus: string | null;
  assignedToId: string | null;
  updateVersion?: number;
  isCreator: boolean;
  isAssignee: boolean;
  isViewingDraft?: boolean;
}

export default function BriefActions({
  briefId,
  type,
  upstreamState,
  downstreamState,
  title,
  content,
  priority,
  estimatedManDays,
  expectedCompletionAt,
  currentVersionStatus,
  assignedToId,
  updateVersion,
  isCreator,
  isAssignee,
  isViewingDraft,
}: BriefActionsProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Edit / update form state
  const [editMode, setEditMode] = useState<"patch" | "update">("patch");
  const [editTitle, setEditTitle] = useState(title);
  const [editType, setEditType] = useState<BriefType>(type);
  const [editContent, setEditContent] = useState(content);
  const [editPriority, setEditPriority] = useState(priority);
  const [editEstimated, setEditEstimated] = useState(estimatedManDays?.toString() || "");
  const [editExpectedCompletion, setEditExpectedCompletion] = useState(
    isoToLocalDateTime(expectedCompletionAt)
  );
  const [editReason, setEditReason] = useState("");

  // Modal state
  const [modal, setModal] = useState<
    | null
    | "edit"
    | "send"
    | "reject"
    | "cancel"
    | "suspend"
    | "resume"
    | "review"
    | "approve"
    | "reject_submit"
    | "process"
    | "submit"
    | "open"
    | "delegate"
    | "block"
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

  const startEdit = (mode: "patch" | "update") => {
    setEditMode(mode);
    setEditTitle(title);
    setEditType(type);
    setEditContent(content);
    setEditPriority(priority);
    setEditEstimated(estimatedManDays?.toString() || "");
    setEditExpectedCompletion(isoToLocalDateTime(expectedCompletionAt));
    setEditReason("");
    setModal("edit");
  };

  const handleEditSave = async () => {
    if (!isNonEmpty(editTitle) || !isNonEmpty(editContent)) {
      setError("标题和内容不能为空");
      return;
    }

    const payload: Record<string, unknown> = {
      title: editTitle.trim(),
      type: editType,
      content: editContent.trim(),
      priority: editPriority,
      estimated_man_days: editEstimated ? parseFloat(editEstimated) : null,
      expected_completion_at: editExpectedCompletion
        ? localDateTimeToISO(editExpectedCompletion)
        : null,
      revision_reason: editReason.trim() || (editMode === "patch" ? "更新内容" : "版本更新"),
    };

    if (editMode === "update") {
      if (updateVersion === undefined) {
        setError("缺少更新版本号");
        return;
      }
      payload.version = updateVersion;
    }

    const path =
      editMode === "patch"
        ? `/api/briefs/${briefId}/editing?action=patch`
        : `/api/briefs/${briefId}/upstream-actions?action=update`;

    setLoading(true);
    setError(null);
    const result = await apiFetch(path, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setLoading(false);

    if (!result.ok) {
      setError(result.message);
      return;
    }

    setModal(null);
    router.refresh();
  };

  const handleReview = async () => {
    await handleAction(`/api/briefs/${briefId}/editing?action=submit-review`, { note: note.trim() || undefined });
    setModal(null);
    setNote("");
  };

  const handleSend = async () => {
    if (sendMode === "registered") {
      if (!selectedUserId) {
        setError("请选择 downstream 用户");
        return;
      }
      await handleAction(`/api/briefs/${briefId}/transfer?action=send`, {
        assigned_to: selectedUserId,
        note: note.trim() || undefined,
      });
      resetSendModal();
      setModal(null);
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
      setModal(null);
      router.refresh();
    }
  };

  const handleReject = async () => {
    if (!isNonEmpty(reason)) {
      setError("请填写拒绝原因");
      return;
    }
    await handleAction(`/api/briefs/${briefId}/transfer?action=reject`, { reason: reason.trim() });
    setModal(null);
    setReason("");
  };

  const handleUpstreamReasonAction = async (action: string) => {
    if (!isNonEmpty(reason)) {
      setError("请填写说明");
      return;
    }
    await handleAction(`/api/briefs/${briefId}/upstream-actions?action=${action}`, {
      content: reason.trim(),
    });
    setModal(null);
    setReason("");
  };

  const handleDownstreamAction = async (action: string, requireReason: boolean) => {
    if (requireReason && !isNonEmpty(reason)) {
      setError("请填写说明");
      return;
    }
    await handleAction(`/api/briefs/${briefId}/downstream-actions?action=${action}`, {
      content: reason.trim() || undefined,
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

  const modalTitle = () => {
    switch (modal) {
      case "send":
        return "发送给 downstream";
      case "edit":
        return editMode === "patch" ? "编辑 Brief" : "更新版本";
      case "review":
        return "提交审查";
      case "reject":
        return "拒绝 Brief";
      case "cancel":
        return "取消 Brief";
      case "suspend":
        return "暂停 Brief";
      case "resume":
        return "恢复 Brief";
      case "approve":
        return "确认完成";
      case "reject_submit":
        return "打回完成";
      case "process":
        return "进度更新";
      case "submit":
        return "提交完成";
      case "open":
        return "重新打开";
      case "delegate":
        return "委托说明";
      case "block":
        return "标记阻塞";
      default:
        return "";
    }
  };

  const renderModal = () => {
    if (!modal) return null;

    return (
      <div className="modal-overlay" onClick={closeModal}>
        <div className={`modal-card ${modal === "edit" ? "modal-wide" : ""}`} onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>{modalTitle()}</h3>
            <button className="btn btn-sm" onClick={closeModal}>关闭</button>
          </div>

          <div className="modal-body">
            {error && <div className="error-message mb-12">{error}</div>}

            {modal === "edit" && (
              <>
                <div className="form-group">
                  <label className="form-label">标题</label>
                  <input
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    disabled={loading}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">类型</label>
                  <select
                    value={editType}
                    onChange={(e) => setEditType(e.target.value as BriefType)}
                    disabled={loading}
                  >
                    <option value="idea">{BRIEF_TYPE_LABELS.idea}</option>
                    <option value="epic">{BRIEF_TYPE_LABELS.epic}</option>
                    <option value="feature">{BRIEF_TYPE_LABELS.feature}</option>
                    <option value="story">{BRIEF_TYPE_LABELS.story}</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">内容</label>
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    rows={10}
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
                <div className="form-group">
                  <label className="form-label">预期完成时间</label>
                  <input
                    type="datetime-local"
                    value={editExpectedCompletion}
                    onChange={(e) => setEditExpectedCompletion(e.target.value)}
                    disabled={loading}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">变更原因</label>
                  <input
                    type="text"
                    value={editReason}
                    onChange={(e) => setEditReason(e.target.value)}
                    placeholder={editMode === "patch" ? "更新内容" : "版本更新原因"}
                    disabled={loading}
                  />
                </div>
              </>
            )}

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

            {modal === "process" && (
              <div className="form-group">
                <label className="form-label">进度说明（可选）</label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={5}
                  placeholder="填写最新进度..."
                />
              </div>
            )}

            {[
              "review",
              "reject",
              "cancel",
              "suspend",
              "resume",
              "approve",
              "reject_submit",
              "submit",
              "open",
              "delegate",
              "block",
            ].includes(modal) && (
              <div className="form-group">
                <label className="form-label">
                  {modal === "review"
                    ? "审查备注"
                    : modal === "reject"
                      ? "拒绝原因"
                      : modal === "cancel"
                      ? "取消原因"
                      : modal === "suspend"
                        ? "暂停原因"
                        : modal === "resume"
                          ? "恢复原因"
                          : modal === "approve"
                            ? "确认备注"
                            : modal === "reject_submit"
                              ? "打回原因"
                              : modal === "submit"
                                ? "完成说明"
                                : modal === "open"
                                  ? "重新打开原因"
                                  : modal === "delegate"
                                    ? "委托说明"
                                    : "阻塞原因"}
                  {modal !== "delegate" && modal !== "approve" && modal !== "review" && " *"}
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
                onClick={() => {
                  if (modal === "edit") return handleEditSave();
                  if (modal === "send") return handleSend();
                  if (modal === "review") return handleReview();
                  if (modal === "reject") return handleReject();
                  if (modal === "process") return handleDownstreamAction("process", false);
                  if (modal === "submit") return handleDownstreamAction("submit", true);
                  if (modal === "open") return handleDownstreamAction("open", true);
                  if (modal === "delegate") return handleDownstreamAction("delegate", false);
                  if (modal === "block") return handleDownstreamAction("block", true);
                  return handleUpstreamReasonAction(modal);
                }}
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

  const renderDraftActions = () => {
    if (!isViewingDraft) return null;
    if (!isCreator) return null;

    if (currentVersionStatus === "draft") {
      return (
        <div className="detail-header-actions-group">
          <button
            className="btn btn-sm"
            onClick={() => startEdit("patch")}
            disabled={loading}
          >
            修改
          </button>
          <button
            className="btn btn-sm btn-primary"
            onClick={() => setModal("review")}
            disabled={loading}
          >
            审核
          </button>
        </div>
      );
    }

    if (currentVersionStatus === "reviewed") {
      if (assignedToId === null) {
        return (
          <div className="detail-header-actions-group">
            <button
              className="btn btn-sm"
              onClick={() => startEdit("patch")}
              disabled={loading}
            >
              修改
            </button>
            <button
              className="btn btn-sm btn-primary"
              onClick={() => setModal("send")}
              disabled={loading}
            >
              分配用户
            </button>
          </div>
        );
      }

      return (
        <div className="detail-header-actions-group">
          <button
            className="btn btn-sm"
            onClick={() => startEdit("patch")}
            disabled={loading}
          >
            修改
          </button>
          <button
            className="btn btn-sm btn-primary"
            onClick={() => {
              if (updateVersion === undefined) {
                setError("缺少更新版本号");
                return;
              }
              handleAction(`/api/briefs/${briefId}/upstream-actions?action=update`, {
                version: updateVersion,
                content: "发送更新",
              });
            }}
            disabled={loading}
          >
            更新
          </button>
        </div>
      );
    }

    return null;
  };

  const renderDownstreamActions = () => {
    if (!isAssignee) return null;

    if (upstreamState === "sent") {
      return (
        <div className="detail-header-actions-group">
          <button
            className="btn btn-sm btn-primary"
            onClick={() => handleAction(`/api/briefs/${briefId}/transfer?action=accept`)}
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
        </div>
      );
    }

    if (["in_process", "suspended"].includes(upstreamState)) {
      return (
        <div className="detail-header-actions-group">
          {downstreamState !== "opened" && (
            <button
              className="btn btn-sm"
              onClick={() => setModal("open")}
              disabled={loading}
            >
              待处理
            </button>
          )}
          {downstreamState !== "delegated" && (
            <button
              className="btn btn-sm"
              onClick={() => setModal("delegate")}
              disabled={loading}
            >
              已安排
            </button>
          )}
          {downstreamState !== "blocked" && (
            <button
              className="btn btn-sm btn-danger"
              onClick={() => setModal("block")}
              disabled={loading}
            >
              遇阻
            </button>
          )}
          {downstreamState !== "submitted" && (
            <button
              className="btn btn-sm btn-primary"
              onClick={() => setModal("submit")}
              disabled={loading}
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

  const renderUpstreamActions = () => {
    if (!isCreator) return null;

    if (["cancelled", "done"].includes(upstreamState)) {
      return null;
    }

    // Submitted downstream takes priority over general upstream actions.
    if (
      downstreamState === "submitted" &&
      ["in_process", "suspended"].includes(upstreamState)
    ) {
      return (
        <div className="detail-header-actions-group">
          <button
            className="btn btn-sm btn-primary"
            onClick={() => setModal("approve")}
            disabled={loading}
          >
            确认完成
          </button>
          <button
            className="btn btn-sm btn-danger"
            onClick={() => setModal("reject_submit")}
            disabled={loading}
          >
            拒绝结果
          </button>
        </div>
      );
    }

    if (upstreamState === "sent") {
      return (
        <div className="detail-header-actions-group">
          <button
            className="btn btn-sm"
            onClick={() => startEdit("patch")}
            disabled={loading}
          >
            修改
          </button>
          <button
            className="btn btn-sm btn-danger"
            onClick={() => setModal("cancel")}
            disabled={loading}
          >
            取消
          </button>
        </div>
      );
    }

    if (upstreamState === "in_process") {
      return (
        <div className="detail-header-actions-group">
          <button
            className="btn btn-sm"
            onClick={() => startEdit("patch")}
            disabled={loading}
          >
            修改
          </button>
          <button
            className="btn btn-sm"
            onClick={() => setModal("suspend")}
            disabled={loading}
          >
            暂停
          </button>
          <button
            className="btn btn-sm btn-danger"
            onClick={() => setModal("cancel")}
            disabled={loading}
          >
            取消
          </button>
        </div>
      );
    }

    if (upstreamState === "suspended") {
      return (
        <div className="detail-header-actions-group">
          <button
            className="btn btn-sm"
            onClick={() => startEdit("patch")}
            disabled={loading}
          >
            修改
          </button>
          <button
            className="btn btn-sm btn-primary"
            onClick={() => setModal("resume")}
            disabled={loading}
          >
            恢复
          </button>
          <button
            className="btn btn-sm btn-danger"
            onClick={() => setModal("cancel")}
            disabled={loading}
          >
            取消
          </button>
        </div>
      );
    }

    if (upstreamState === "editing" && currentVersionStatus === "draft") {
      return (
        <div className="detail-header-actions-group">
          <button
            className="btn btn-sm"
            onClick={() => startEdit("patch")}
            disabled={loading}
          >
            修改
          </button>
          <button
            className="btn btn-sm btn-primary"
            onClick={() => setModal("review")}
            disabled={loading}
          >
            审核
          </button>
        </div>
      );
    }

    if (upstreamState === "editing" && currentVersionStatus === "reviewed") {
      return (
        <div className="detail-header-actions-group">
          <button
            className="btn btn-sm"
            onClick={() => startEdit("patch")}
            disabled={loading}
          >
            修改
          </button>
          <button
            className="btn btn-sm btn-primary"
            onClick={() => setModal("send")}
            disabled={loading}
          >
            分配用户
          </button>
        </div>
      );
    }

    if (upstreamState === "editing" && currentVersionStatus === "final") {
      return (
        <div className="detail-header-actions-group">
          <button
            className="btn btn-sm"
            onClick={() => startEdit("patch")}
            disabled={loading}
          >
            修改
          </button>
          <button
            className="btn btn-sm btn-primary"
            onClick={() => setModal("send")}
            disabled={loading}
          >
            分配用户
          </button>
        </div>
      );
    }

    return null;
  };

  return (
    <>
      {isViewingDraft ? renderDraftActions() : (
        <>
          {renderDownstreamActions()}
          {renderUpstreamActions()}
        </>
      )}
      {renderModal()}
    </>
  );
}
