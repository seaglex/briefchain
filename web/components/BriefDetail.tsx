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
  status: string;
  priority: string;
  created_by: UserRef;
  assigned_to: UserRef | null;
  estimated_man_days: number | null;
  current_version: number;
  created_at: string;
  updated_at: string;
  attachments: unknown[];
}

export interface Transfer {
  id: string;
  brief_version: number;
  from_user: UserRef;
  to_user: UserRef;
  sent_at: string;
  accepted_at: string | null;
  rejected_at: string | null;
  rejection_reason: string | null;
}

export interface Feedback {
  id: string;
  type: string;
  from_user: UserRef;
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

const statusClass = (statusValue: string): string => {
  const map: Record<string, string> = {
    draft: "badge-draft",
    reviewed: "badge-reviewed",
    sent: "badge-sent",
    accepted: "badge-accepted",
    done: "badge-done",
    blocked: "badge-blocked",
    cancelled: "badge-cancelled",
    rejected: "badge-rejected",
  };
  return map[statusValue] || "badge-draft";
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
          <span className={`badge ${statusClass(brief.status)}`}>
            {brief.status}
          </span>
          <span className={`badge ${priorityClass(brief.priority)}`}>
            {brief.priority.toUpperCase()}
          </span>
        </div>
        {actions && <div className="flex items-center gap-8">{actions}</div>}
      </div>

      <div className="detail-tabs">
        <div className="detail-tab active">内容</div>
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
                        <strong>{transfer.from_user.name}</strong> 发送给{" "}
                        <strong>{transfer.to_user.name}</strong>
                      </span>
                      <span
                        className={`badge ${statusClass(
                          transfer.accepted_at
                            ? "accepted"
                            : transfer.rejected_at
                              ? "rejected"
                              : "sent"
                        )}`}
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
                        : feedback.type === "completion"
                          ? "var(--c-green-bg)"
                          : "var(--c-primary-bg)",
                    color:
                      feedback.type === "blocked"
                        ? "var(--c-amber)"
                        : feedback.type === "completion"
                          ? "var(--c-green)"
                          : "var(--c-primary)",
                  }}
                >
                  {feedback.type === "blocked" ? "!" : feedback.type === "completion" ? "✓" : "•"}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span>
                      <strong>{feedback.type}</strong> — {feedback.from_user.name}
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
        创建者：{brief.created_by.name} | 执行者：{brief.assigned_to?.name || "--"} | 版本：v
        {brief.current_version}
      </div>
    </div>
  );
}
