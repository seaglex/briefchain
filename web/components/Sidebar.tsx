"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/auth";

interface SidebarProps {
  currentUserName?: string;
}

export default function Sidebar({ currentUserName = "用户" }: SidebarProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const role = searchParams.get("role") || "assigned";

  const navItemClass = (active: boolean) =>
    `nav-item ${active ? "active" : ""}`;

  const handleLogout = async () => {
    await apiFetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  };

  return (
    <div className="sidebar">
      <Link href="/briefs?role=assigned" className="brand" style={{ textDecoration: "none" }}>
        <div className="brand-icon">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M20.42 4.58a5.4 5.4 0 0 0-7.65 0l-.77.78-.77-.78a5.4 5.4 0 0 0-7.65 7.65l.77.78 7.65 7.65 7.65-7.65.77-.78a5.4 5.4 0 0 0 0-7.65z" />
          </svg>
        </div>
        <div className="brand-name">BriefChain</div>
      </Link>

      <nav className="nav">
        <Link href="/briefs/new" className="nav-create">
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          创建 Brief
        </Link>

        <div className="nav-divider" />

        <Link
          href="/briefs?role=created"
          className={navItemClass(
            pathname === "/briefs" && role === "created"
          )}
        >
          <span>我创建的</span>
        </Link>
        <Link
          href="/briefs?role=assigned"
          className={navItemClass(
            pathname === "/briefs" && role === "assigned"
          )}
        >
          <span>分配给我的</span>
        </Link>

        <div className="nav-divider" />

        <div className={navItemClass(false)}>
          <span>所有 chains</span>
        </div>
        <div className={navItemClass(false)}>
          <span>工作看板</span>
        </div>

        <div className="nav-divider" />

        <div className={navItemClass(false)}>
          <span>设置</span>
        </div>
      </nav>

      <div
        style={{
          padding: "12px 20px",
          borderTop: "0.5px solid var(--c-border)",
          display: "flex",
          alignItems: "center",
          gap: 8,
          cursor: "pointer",
        }}
        onClick={handleLogout}
      >
        <div className="avatar-sm">{currentUserName.slice(0, 2).toUpperCase()}</div>
        <span className="text-2">{currentUserName}</span>
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ color: "var(--c-text-3)", marginLeft: "auto" }}
        >
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
      </div>
    </div>
  );
}
