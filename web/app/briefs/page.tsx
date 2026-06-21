import { redirect } from "next/navigation";
import Link from "next/link";
import { serverFetch, getCurrentUser } from "@/lib/server-auth";
import BriefFilters, { BriefTabs } from "@/components/BriefFilters";
import Sidebar from "@/components/Sidebar";

interface BriefListItem {
  brief_id: string;
  title: string;
  status: string;
  priority: string;
  created_by: { id: string; name: string };
  assigned_to: { id: string; name: string } | null;
  updated_at: string;
}

interface BriefListResponse {
  briefs: BriefListItem[];
  next_cursor: string | null;
}

export default async function BriefListPage({
  searchParams,
}: {
  searchParams: Promise<{ role?: string; status?: string; priority?: string }>;
}) {
  const { role: rawRole, status, priority } = await searchParams;
  const role = rawRole === "created" ? "created" : "assigned";

  const [userResult, briefsResult] = await Promise.all([
    getCurrentUser(),
    serverFetch<BriefListResponse>(
      `/api/v1/briefs?role=${role}${status ? `&status=${status}` : ""}&page_size=100`
    ),
  ]);

  if (!userResult.ok) {
    redirect("/login");
  }

  let briefs = briefsResult.ok ? briefsResult.data.briefs : [];
  if (priority) {
    briefs = briefs.filter((b) => b.priority === priority);
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

  return (
    <div className="app">
      <Sidebar currentUserName={userResult.user.name} />
      <div className="main">
        <div className="topbar">
          <div className="flex items-center gap-8">
            <h2>{role === "assigned" ? "分配给我的" : "我创建的"}</h2>
          </div>
          <div className="flex items-center gap-12">
            <Link href="/briefs/new" className="btn btn-primary btn-sm">
              新建
            </Link>
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
                    <span className={`badge ${statusClass(brief.status)}`}>
                      {brief.status}
                    </span>
                    <span>
                      assigned: {brief.assigned_to?.name || "--"}
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
      </div>
    </div>
  );
}
