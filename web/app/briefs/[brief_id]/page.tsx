import { redirect } from "next/navigation";
import { serverFetch, getCurrentUser } from "@/lib/server-auth";
import BriefActions from "@/components/BriefActions";
import BriefDetailView, { BriefDetail, Transfer, Feedback } from "@/components/BriefDetail";
import AppShell from "@/components/AppShell";
import HeaderUser from "@/components/HeaderUser";

export default async function BriefDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ brief_id: string }>;
  searchParams: Promise<{ version?: string }>;
}) {
  const { brief_id } = await params;
  const { version: versionQuery } = await searchParams;
  const viewingVersion = versionQuery ? parseInt(versionQuery, 10) : null;

  const [userResult, baseBriefResult, detailResult, transfersResult, feedbacksResult] = await Promise.all([
    getCurrentUser(),
    serverFetch<BriefDetail>(`/api/v1/briefs/${brief_id}`),
    viewingVersion
      ? serverFetch<BriefDetail>(`/api/v1/briefs/${brief_id}?version=${viewingVersion}`)
      : serverFetch<BriefDetail>(`/api/v1/briefs/${brief_id}`),
    serverFetch<Transfer[]>(`/api/v1/briefs/${brief_id}/transfers`),
    serverFetch<Feedback[]>(`/api/v1/briefs/${brief_id}/feedbacks`),
  ]);

  const baseBrief = baseBriefResult.ok ? baseBriefResult.data : null;
  const brief = detailResult.ok ? detailResult.data : null;
  const transfers = transfersResult.ok ? transfersResult.data : [];
  const feedbacks = feedbacksResult.ok ? feedbacksResult.data : [];

  if (!userResult.ok) {
    redirect("/login");
  }

  if (!brief || !baseBrief) {
    return (
      <AppShell userType={userResult.user.user_type}>
        <div className="content">
          <div className="empty-state">Brief 不存在或无权限访问</div>
        </div>
      </AppShell>
    );
  }

  const currentUserId = userResult.user.id;
  const isCreator = baseBrief.created_by_id === currentUserId;
  const isAssignee = baseBrief.assigned_to_id === currentUserId;
  const isViewingDraft = viewingVersion !== null && viewingVersion === baseBrief.unfinalized_version;
  const updateVersion = isViewingDraft ? brief.version : baseBrief.unfinalized_version;

  return (
    <AppShell userType={userResult.user.user_type}>
      <div className="topbar">
        <div className="flex items-center gap-8">
          <h2>{isViewingDraft ? "Draft 版本" : "Brief 详情"}</h2>
        </div>
        <div className="flex items-center gap-12">
          <HeaderUser userName={userResult.user.name} />
        </div>
      </div>

      <div className="content">
        <BriefDetailView
          brief={brief}
          transfers={transfers}
          feedbacks={feedbacks}
          isViewingDraft={isViewingDraft}
          baseBrief={baseBrief}
          isCreator={isCreator}
          currentUserId={currentUserId}
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
              assignedToId={baseBrief.assigned_to_id}
              updateVersion={updateVersion ?? undefined}
              isCreator={isCreator}
              isAssignee={isAssignee}
              isViewingDraft={isViewingDraft}
            />
          }
        />
      </div>
    </AppShell>
  );
}
