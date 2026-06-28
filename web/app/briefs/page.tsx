import { redirect } from "next/navigation";
import Link from "next/link";
import { serverFetch, getCurrentUser } from "@/lib/server-auth";
import BriefFilters, { BriefTabs } from "@/components/BriefFilters";
import AppShell from "@/components/AppShell";
import HeaderUser from "@/components/HeaderUser";

interface BriefListItem {
  brief_id: string;
  title: string;
  upstream_state: string;
  downstream_state: string | null;
  priority: string;
  created_by_name: string;
  assigned_to_name: string | null;
  updated_at: string;
}

interface BriefListResponse {
  briefs: BriefListItem[];
  next_cursor: string | null;
}

const ROLE_LABELS: Record<string, string> = {
  assigned: "分配给我",
  created: "我创建的",
  pending: "待处理",
};

export default async function BriefListPage({
  searchParams,
}: {
  searchParams: Promise<{ role?: string; upstream_state?: string; downstream_state?: string; priority?: string }>;
}) {
  const { role: rawRole, upstream_state, downstream_state, priority } = await searchParams;
  const role = ["created", "assigned", "pending"].includes(rawRole || "")
    ? (rawRole as "created" | "assigned" | "pending")
    : "assigned";
  const isPending = role === "pending";

  const queryParts: string[] = [];
  if (isPending) {
    queryParts.push("role=assigned");
    queryParts.push("upstream_state=in_process");
  } else {
    queryParts.push(`role=${role}`);
    if (upstream_state) queryParts.push(`upstream_state=${upstream_state}`);
    if (downstream_state) queryParts.push(`downstream_state=${downstream_state}`);
  }
  queryParts.push("page_size=100");

  const [userResult, briefsResult] = await Promise.all([
    getCurrentUser(),
    serverFetch<BriefListResponse>(`/api/v1/briefs?${queryParts.join("&")}`),
  ]);

  if (!userResult.ok) {
    redirect("/login");
  }

  let briefs = briefsResult.ok ? briefsResult.data.briefs : [];
  if (isPending) {
    briefs = briefs.filter((b) => b.downstream_state !== "submitted");
  }
  if (priority) {
    briefs = briefs.filter((b) => b.priority === priority);
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

  return (
    <AppShell userType={userResult.user.user_type}>
      <div className="topbar">
        <div className="flex items-center gap-8">
          <h2>{ROLE_LABELS[role]}</h2>
        </div>
        <div className="flex items-center gap-12">
          <HeaderUser userName={userResult.user.name} />
        </div>
      </div>

      <div className="content">
        <BriefTabs currentRole={role} />
        <BriefFilters />

        {!briefsResult.ok && (
          <div className="error-message">{(briefsResult as { message: string }).message}</div>
        )}

        {briefs.length === 0 && (
          <div className="empty-state">
            <p>暂无 Brief</p>
          </div>
        )}

        {briefs.map((brief) => (
          <Link
            key={brief.brief_id}
            href={`/briefs/${brief.brief_id}`}
            className="card card-clickable"
            style={{ textDecoration: "none", color: "inherit" }}
          >
            <div className="brief-item">
              <div className="flex-1">
                <div className="brief-title">{brief.title}</div>
                <div className="brief-meta mt-8">
                  <span className={`badge ${priorityClass(brief.priority)}`}>
                    {brief.priority.toUpperCase()}
                  </span>
                  <span className={`badge ${upstreamStateClass(brief.upstream_state)}`}>
                    {brief.upstream_state}
                  </span>
                  {brief.downstream_state && (
                    <span className={`badge ${downstreamStateClass(brief.downstream_state)}`}>
                      {brief.downstream_state}
                    </span>
                  )}
                  <span>
                    assigned: {brief.assigned_to_name || "--"}
                  </span>
                </div>
              </div>
              <div className="text-3" style={{ fontSize: 12 }}>
                {new Date(brief.updated_at).toLocaleString("zh-CN")}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
