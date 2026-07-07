import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/server-auth";
import AppShell from "@/components/AppShell";
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
      <TaskDetail taskId={parseInt(taskId, 10)} currentUserId={userResult.user.id} userName={userResult.user.name} />
    </AppShell>
  );
}
