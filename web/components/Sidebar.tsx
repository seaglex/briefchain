"use client";

import Link from "next/link";
import { Suspense } from "react";
import { usePathname, useSearchParams } from "next/navigation";

function SidebarInner() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const role = searchParams.get("role") || "assigned";

  const navItemClass = (active: boolean) =>
    `nav-item ${active ? "active" : ""}`;

  return (
    <div className="sidebar">
      <Link href="/landing" className="brand" style={{ textDecoration: "none" }}>
        <div className="brand-name">BriefChain</div>
      </Link>

      <nav className="nav">
        <Link href="/briefs/new" className="nav-create">
          + 创建 Brief
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
          <span>分配给我</span>
        </Link>
        <Link
          href="/briefs?role=pending"
          className={navItemClass(
            pathname === "/briefs" && role === "pending"
          )}
        >
          <span>待处理</span>
        </Link>

        <div className="nav-divider" />

        <div className={navItemClass(false)}>
          <span>Chains（未实现）</span>
        </div>

        <div className="nav-divider" />

        <Link
          href="/kanban?create=true"
          className={navItemClass(false)}
        >
          <span>创建 Task</span>
        </Link>
        <Link
          href="/kanban"
          className={navItemClass(pathname === "/kanban" || pathname === "/kanban/config")}
        >
          <span>个人 kanban</span>
        </Link>

        <div className="nav-divider" />

        <div className={navItemClass(false)}>
          <span>设置（未实现）</span>
        </div>
      </nav>
    </div>
  );
}

export default function Sidebar() {
  return (
    <Suspense fallback={<div className="sidebar" />}>
      <SidebarInner />
    </Suspense>
  );
}
