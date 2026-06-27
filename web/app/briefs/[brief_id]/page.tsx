import { redirect } from "next/navigation";
import Link from "next/link";
import { serverFetch, getCurrentUser } from "@/lib/server-auth";
import BriefActions from "@/components/BriefActions";
import BriefDetailView, { BriefDetail, Transfer, Feedback } from "@/components/BriefDetail";
import Sidebar from "@/components/Sidebar";

async function fetchBriefDetail(briefId: string): Promise<BriefDetail | null> {
  const result = await serverFetch<BriefDetail>(`/api/v1/briefs/${briefId}`);
  return result.ok ? result.data : null;
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
    serverFetch<BriefDetail>(`/api/v1/briefs/${brief_id}`),
    serverFetch<Transfer[]>(`/api/v1/briefs/${brief_id}/transfers`),
    serverFetch<Feedback[]>(`/api/v1/briefs/${brief_id}/feedbacks`),
  ]);

  const brief = detailResult.ok ? detailResult.data : null;
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
  const isCreator = brief.created_by_id === currentUserId;
  const isAssignee = brief.assigned_to_id === currentUserId;

  return (
    <div className="app">
      <Sidebar currentUserName={userResult.user.name} />
      <div className="main">
        <div className="topbar">
          <div className="flex items-center gap-8">
            <Link href={isCreator ? "/briefs?role=created" : "/briefs?role=assigned"} className="btn btn-sm">
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
          <BriefDetailView
            brief={brief}
            transfers={transfers}
            feedbacks={feedbacks}
            actions={
              <BriefActions
                briefId={brief.brief_id}
                upstreamState={brief.upstream_state}
                downstreamState={brief.downstream_state}
                content={brief.content}
                title={brief.title}
                priority={brief.priority}
                estimatedManDays={brief.estimated_man_days}
                expectedCompletionAt={brief.expected_completion_at}
                currentVersionStatus={brief.current_version_status}
                isCreator={isCreator}
                isAssignee={isAssignee}
              />
            }
          />
        </div>
      </div>
    </div>
  );
}
