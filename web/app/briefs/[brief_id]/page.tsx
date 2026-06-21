import { redirect } from "next/navigation";
import Link from "next/link";
import { serverFetch, getCurrentUser } from "@/lib/server-auth";
import BriefActions from "@/components/BriefActions";
import Sidebar from "@/components/Sidebar";

interface UserRef {
  id: string;
  name: string;
}

interface BriefDetail {
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

interface Transfer {
  id: string;
  brief_version: number;
  from_user: UserRef;
  to_user: UserRef;
  sent_at: string;
  accepted_at: string | null;
  rejected_at: string | null;
  rejection_reason: string | null;
}

interface Feedback {
  id: string;
  type: string;
  from_user: UserRef;
  content: string;
  created_at: string;
}

async function fetchBriefDetail(briefId: string): Promise<BriefDetail | null> {
  const result = await serverFetch<{ brief: BriefDetail }>(`/api/v1/briefs/${briefId}`);
  return result.ok ? result.data.brief : null;
}

async function fetchTransfers(briefId: string): Promise<Transfer[]> {
  const result = await serverFetch<Transfer[]>(`/api/v1/briefs/${briefId}/transfers`);
  return result.ok ? result.data : [];
}

async function fetchFeedbacks(briefId: string): Promise<Feedback[]> {
  const result = await serverFetch<Feedback[]>(`/api/v1/briefs/${briefId}/feedbacks`);
  return result.ok ? result.data : [];
}

export default async function BriefDetailPage({
  params,
}: {
  params: Promise<{ brief_id: string }>;
}) {
  const { brief_id } = await params;

  const [userResult, detailResult, transfersResult, feedbacksResult] = await Promise.all([
    getCurrentUser(),
    serverFetch<{ brief: BriefDetail }>(`/api/v1/briefs/${brief_id}`),
    serverFetch<Transfer[]>(`/api/v1/briefs/${brief_id}/transfers`),
    serverFetch<Feedback[]>(`/api/v1/briefs/${brief_id}/feedbacks`),
  ]);

  const brief = detailResult.ok ? detailResult.data.brief : null;
  const transfers = transfersResult.ok ? transfersResult.data : [];
  const feedbacks = feedbacksResult.ok ? feedbacksResult.data : [];

  if (!userResult.ok) {
    redirect("/login");
  }

  if (!brief) {
    return (
      <div className="app">
        <div className="main">
          <div className="content">
            <div className="empty-state">Brief 不存在或无权限访问</div>
          </div>
        </div>
      </div>
    );
  }

  const currentUserId = userResult.user.id;
  const isCreator = brief.created_by.id === currentUserId;
  const isAssignee = brief.assigned_to?.id === currentUserId;

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

  return (
    <div className="app">
      <Sidebar currentUserName={userResult.user.name} />
      <div className="main">
        <div className="topbar">
          <div className="flex items-center gap-8">
            <Link href="/briefs?role=assigned" className="btn btn-sm">
              ← 返回
            </Link>
            <h2>Brief 详情</h2>
          </div>
          <div className="flex items-center gap-12">
            <Link href="/briefs/new" className="btn btn-primary btn-sm">
              新建
            </Link>
          </div>
        </div>

        <div className="content">
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
            <BriefActions
              briefId={brief.brief_id}
              status={brief.status}
              content={brief.content}
              title={brief.title}
              priority={brief.priority}
              estimatedManDays={brief.estimated_man_days}
              isCreator={isCreator}
              isAssignee={isAssignee}
            />
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
                          <span className={`badge ${statusClass(
                            transfer.accepted_at
                              ? "accepted"
                              : transfer.rejected_at
                                ? "rejected"
                                : "sent"
                          )}`}>
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

          <div
            className="mt-16 text-3"
            style={{ fontSize: 12 }}
          >
            创建者：{brief.created_by.name} | 执行者：{brief.assigned_to?.name || "--"} | 版本：v
            {brief.current_version}
          </div>
        </div>
      </div>
    </div>
  );
}
