import type { ReactNode } from "react";

export interface UserRef {
  id: string;
  name: string;
}

export interface BriefDetail {
  brief_id: string;
  root_id: string;
  parent_id: string | null;
  title: string;
  content: string;
  upstream_state: string;
  downstream_state: string | null;
  priority: string;
  created_by_id: string;
  created_by_name: string;
  assigned_to_id: string | null;
  assigned_to_name: string | null;
  estimated_man_days: number | null;
  expected_completion_at: string | null;
  current_version: number | null;
  current_version_status: string | null;
  version: number;
  is_current: boolean;
  draft_version: number | null;
  status_changed_by_id: string;
  status_changed_by_name: string;
  status_changed_at: string;
  created_at: string;
  updated_at: string;
  attachments: unknown[];
}

export interface Transfer {
  id: string;
  brief_version: number;
  from_user_id: string;
  from_user_name: string;
  to_user_id: string;
  to_user_name: string;
  sent_at: string;
  accepted_at: string | null;
  rejected_at: string | null;
  rejection_reason: string | null;
}

export interface Feedback {
  id: string;
  type: string;
  is_to_down: boolean;
  from_user_id: string;
  from_user_name: string;
  to_user_id: string;
  to_user_name: string;
  content: string;
  created_at: string;
}

interface BriefDetailViewProps {
  brief: BriefDetail;
  transfers: Transfer[];
  feedbacks: Feedback[];
  actions?: React.ReactNode;
  readOnly?: boolean;
}

const upstreamStateClass = (stateValue: string): string => {
  const map: Record<string, string> = {
    editing: "badge-draft",
    reviewed: "badge-reviewed",
    sent: "badge-sent",
    in_process: "badge-accepted",
    suspended: "badge-blocked",
    cancelled: "badge-cancelled",
    done: "badge-done",
  };
  return map[stateValue] || "badge-draft";
};

const downstreamStateClass = (stateValue: string): string => {
  const map: Record<string, string> = {
    opened: "badge-accepted",
    submitted: "badge-reviewed",
    delegated: "badge-sent",
    blocked: "badge-blocked",
  };
  return map[stateValue] || "badge-accepted";
};

const priorityClass = (p: string): string => {
  if (p === "p0" || p === "p1") return "badge-p1";
  if (p === "p2") return "badge-p2";
  return "badge-p3";
};

export default function BriefDetailView({
  brief,
  transfers,
  feedbacks,
  actions,
  readOnly,
}: BriefDetailViewProps) {
  return (
    <div data-readonly={readOnly}>
      <div className="detail-header">
        <div className="flex items-center gap-12">
          <h1>{brief.title}</h1>
          <span className={`badge ${upstreamStateClass(brief.upstream_state)}`}>
            {brief.upstream_state}
          </span>
          {brief.current_version_status && (
            <span className={`badge ${upstreamStateClass(brief.current_version_status)}`}>
              {brief.current_version_status}
            </span>
          )}
          {brief.downstream_state && (
            <span className={`badge ${downstreamStateClass(brief.downstream_state)}`}>
              {brief.downstream_state}
            </span>
          )}
          {brief.draft_version && (
            <span className="badge badge-draft">Draft v{brief.draft_version}</span>
          )}
          <span className={`badge ${priorityClass(brief.priority)}`}>
            {brief.priority.toUpperCase()}
          </span>
        </div>
        {actions && <div className="flex items-center gap-8">{actions}</div>}
      </div>

      <div className="detail-tabs">
        <div className="detail-tab active">内容</div>
        <div className="detail-tab">流转</div>
        <div className="detail-tab">Feedback</div>
      </div>

      <div className="card">
        <div className="detail-content">
          <h3 className="mb-12">内容</h3>
          <p style={{ whiteSpace: "pre-wrap" }}>{brief.content}</p>

          {brief.estimated_man_days !== null && (
            <>
              <h3 className="mb-12 mt-16">预估人天</h3>
              <p>{brief.estimated_man_days}</p>
            </>
          )}

          {brief.expected_completion_at && (
            <>
              <h3 className="mb-12 mt-16">预期完成时间</h3>
              <p>{new Date(brief.expected_completion_at).toLocaleString("zh-CN")}</p>
            </>
          )}
        </div>
      </div>

      <div style={{ marginTop: 24 }}>
        <h3 className="mb-12">流转历史</h3>
        {transfers.length === 0 ? (
          <div className="card text-3">暂无流转记录</div>
        ) : (
          <div className="card">
            <div className="timeline">
              {transfers.map((transfer, index) => (
                <div className="timeline-item" key={transfer.id}>
                  <div className="timeline-dot" />
                  {index < transfers.length - 1 && <div className="timeline-line" />}
                  <div className="timeline-content">
                    <div className="flex items-center justify-between">
                      <span>
                        <strong>{transfer.from_user_name}</strong> 发送给{" "}
                        <strong>{transfer.to_user_name}</strong>
                      </span>
                      <span
                        className={`badge ${
                          transfer.accepted_at
                            ? "badge-accepted"
                            : transfer.rejected_at
                              ? "badge-cancelled"
                              : "badge-sent"
                        }`}
                      >
                        {transfer.accepted_at
                          ? "accepted"
                          : transfer.rejected_at
                            ? "rejected"
                            : "sent"}
                      </span>
                    </div>
                    <div className="timeline-time mt-8">
                      {new Date(transfer.sent_at).toLocaleString("zh-CN")} — v
                      {transfer.brief_version}
                    </div>
                    {transfer.rejection_reason && (
                      <div className="mt-8 text-2">
                        原因：{transfer.rejection_reason}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div style={{ marginTop: 24 }}>
        <h3 className="mb-12">Feedback</h3>
        {feedbacks.length === 0 ? (
          <div className="card text-3">暂无 Feedback</div>
        ) : (
          <div className="card">
            {feedbacks.map((feedback) => (
              <div className="feedback-item" key={feedback.id}>
                <div
                  className="feedback-type-icon"
                  style={{
                    background:
                      feedback.type === "blocked"
                        ? "var(--c-amber-bg)"
                        : feedback.type === "submit"
                          ? "var(--c-green-bg)"
                          : "var(--c-primary-bg)",
                    color:
                      feedback.type === "blocked"
                        ? "var(--c-amber)"
                        : feedback.type === "submit"
                          ? "var(--c-green)"
                          : "var(--c-primary)",
                  }}
                >
                  {feedback.type === "blocked" ? "!" : feedback.type === "submit" ? "✓" : "•"}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span>
                      <strong>{feedback.type}</strong>
                      {" "}
                      {feedback.is_to_down ? "→" : "←"}
                      {" "}
                      {feedback.from_user_name} → {feedback.to_user_name}
                    </span>
                    <span className="text-3" style={{ fontSize: 12 }}>
                      {new Date(feedback.created_at).toLocaleString("zh-CN")}
                    </span>
                  </div>
                  <p className="text-2 mt-8">{feedback.content}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-16 text-3" style={{ fontSize: 12 }}>
        创建者：{brief.created_by_name} | 执行者：{brief.assigned_to_name || "--"} | 版本：v
        {brief.version}
      </div>
    </div>
  );
}
