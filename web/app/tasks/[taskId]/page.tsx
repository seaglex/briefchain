import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/server-auth";
import AppShell from "@/components/AppShell";
import HeaderUser from "@/components/HeaderUser";
import TaskDetail from "@/components/TaskDetail";

export default async function TaskDetailPage({
  params,
}: {
  params: Promise<{ taskId: string }>;
}) {
  const { taskId } = await params;
  const userResult = await getCurrentUser();

  if (!userResult.ok) {
    redirect("/login");
  }

  return (
    <AppShell userType={userResult.user.user_type}>
      <div className="topbar">
        <div className="flex items-center gap-8">
          <h2>Task 详情</h2>
        </div>
        <div className="flex items-center gap-12">
          <HeaderUser userName={userResult.user.name} />
        </div>
      </div>

      <TaskDetail taskId={parseInt(taskId, 10)} currentUserId={userResult.user.id} />
    </AppShell>
  );
}
