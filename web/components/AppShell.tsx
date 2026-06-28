import Sidebar from "@/components/Sidebar";

interface AppShellProps {
  userType: string;
  children: React.ReactNode;
}

export default function AppShell({ userType, children }: AppShellProps) {
  const isTemporary = userType === "temporary";

  return (
    <div className="app">
      {!isTemporary && <Sidebar />}
      <div className="main">{children}</div>
    </div>
  );
}
