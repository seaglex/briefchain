import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/server-auth";
import AppShell from "@/components/AppShell";
import HeaderUser from "@/components/HeaderUser";
import NewBriefForm from "@/components/NewBriefForm";

export default async function NewBriefPage() {
  const userResult = await getCurrentUser();

  if (!userResult.ok) {
    redirect("/login");
  }

  return (
    <AppShell userType={userResult.user.user_type}>
      <div className="topbar">
        <div className="flex items-center gap-8">
          <h2>新建 Brief</h2>
        </div>
        <div className="flex items-center gap-12">
          <HeaderUser userName={userResult.user.name} />
        </div>
      </div>

      <div className="content">
        <NewBriefForm />
      </div>
    </AppShell>
  );
}
