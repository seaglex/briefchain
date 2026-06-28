"use client";

import { apiFetch } from "@/lib/auth";

interface HeaderUserProps {
  userName: string;
}

export default function HeaderUser({ userName }: HeaderUserProps) {
  const handleLogout = async () => {
    await apiFetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  };

  return (
    <div className="header-user">
      <div className="avatar-sm">{userName.slice(0, 2).toUpperCase()}</div>
      <span className="text-2">{userName}</span>
      <svg
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        onClick={handleLogout}
        className="logout-icon"
        style={{ color: "var(--c-text-3)", cursor: "pointer" }}
      >
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
        <polyline points="16 17 21 12 16 7" />
        <line x1="21" y1="12" x2="9" y2="12" />
      </svg>
    </div>
  );
}
