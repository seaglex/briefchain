import { redirect } from "next/navigation";
import { Suspense } from "react";
import { getCurrentUser, serverFetch } from "@/lib/server-auth";
import AppShell from "@/components/AppShell";
import KanbanBoard from "@/components/KanbanBoard";
import type { KanbanBoard as KanbanBoardType } from "@/lib/kanban";

export default async function KanbanPage() {
  const userResult = await getCurrentUser();
  if (!userResult.ok) {
    redirect("/login");
  }

  let boardResult = await serverFetch<KanbanBoardType>("/api/v1/kanban/personal");

  if (!boardResult.ok && boardResult.status === 404) {
    const createResult = await serverFetch<{ kanban_id: number }>("/api/v1/kanbans", {
      method: "POST",
      body: JSON.stringify({
        owner_type: "user",
        owner_id: userResult.user.id,
        kanban_template_id: 1,
        group: "none",
        done_visible_days: 14,
        is_default: true,
      }),
    });
    if (createResult.ok) {
      boardResult = await serverFetch<KanbanBoardType>("/api/v1/kanban/personal");
    }
  }

  if (!boardResult.ok) {
    return (
      <AppShell userType={userResult.user.user_type}>
        <div className="topbar">
          <h2>个人 Kanban</h2>
        </div>
        <div className="content">
          <div className="error-message">加载看板失败：{boardResult.message}</div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell userType={userResult.user.user_type}>
      <Suspense fallback={<div className="content">加载中...</div>}>
        <KanbanBoard initialBoard={boardResult.data} currentUserId={userResult.user.id} />
      </Suspense>
    </AppShell>
  );
}
