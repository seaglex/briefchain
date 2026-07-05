import { redirect } from "next/navigation";
import { getCurrentUser, serverFetch } from "@/lib/server-auth";
import AppShell from "@/components/AppShell";
import KanbanConfigForm from "@/components/KanbanConfigForm";
import type {
  KanbanBoard,
  KanbanConfigResponse,
  KanbanTemplateListResponse,
} from "@/lib/kanban";

export default async function KanbanConfigPage() {
  const userResult = await getCurrentUser();
  if (!userResult.ok) {
    redirect("/login");
  }

  const boardResult = await serverFetch<KanbanBoard>("/api/v1/kanban/personal");
  if (!boardResult.ok) {
    return (
      <AppShell userType={userResult.user.user_type}>
        <div className="topbar"><h2>Kanban 配置</h2></div>
        <div className="content">
          <div className="error-message">加载看板失败：{boardResult.message}</div>
        </div>
      </AppShell>
    );
  }

  const kanbanId = boardResult.data.kanban.kanban_id;

  const [configResult, templatesResult] = await Promise.all([
    serverFetch<KanbanConfigResponse>(`/api/v1/kanbans/${kanbanId}`),
    serverFetch<KanbanTemplateListResponse>("/api/v1/kanban-templates"),
  ]);

  if (!configResult.ok) {
    return (
      <AppShell userType={userResult.user.user_type}>
        <div className="topbar"><h2>Kanban 配置</h2></div>
        <div className="content">
          <div className="error-message">加载配置失败：{configResult.message}</div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell userType={userResult.user.user_type}>
      <div className="topbar">
        <h2>Kanban 配置</h2>
      </div>
      <div className="content">
        <KanbanConfigForm
          initialConfig={configResult.data}
          initialTemplates={templatesResult.ok ? templatesResult.data.templates : []}
        />
      </div>
    </AppShell>
  );
}
