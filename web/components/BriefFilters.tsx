"use client";

import { useRouter, useSearchParams } from "next/navigation";

const ROLES = [
  { key: "assigned", label: "分配给我的" },
  { key: "created", label: "我创建的" },
];

const STATUSES = [
  { key: "", label: "全部状态" },
  { key: "draft", label: "draft" },
  { key: "reviewed", label: "reviewed" },
  { key: "sent", label: "sent" },
  { key: "accepted", label: "accepted" },
  { key: "done", label: "done" },
  { key: "blocked", label: "blocked" },
  { key: "cancelled", label: "cancelled" },
];

const PRIORITIES = [
  { key: "", label: "全部优先级" },
  { key: "p0", label: "P0" },
  { key: "p1", label: "P1" },
  { key: "p2", label: "P2" },
  { key: "p3", label: "P3" },
];

export default function BriefFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const role = searchParams.get("role") || "assigned";
  const status = searchParams.get("status") || "";
  const priority = searchParams.get("priority") || "";

  const updateParam = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    // Keep role when changing filters
    if (key !== "role" && !params.has("role")) {
      params.set("role", role);
    }
    router.push(`/briefs?${params.toString()}`);
  };

  return (
    <div className="filter-bar">
      <select
        className="filter-select"
        value={status}
        onChange={(e) => updateParam("status", e.target.value)}
      >
        {STATUSES.map((s) => (
          <option key={s.key} value={s.key}>{s.label}</option>
        ))}
      </select>

      <select
        className="filter-select"
        value={priority}
        onChange={(e) => updateParam("priority", e.target.value)}
      >
        {PRIORITIES.map((p) => (
          <option key={p.key} value={p.key}>{p.label}</option>
        ))}
      </select>
    </div>
  );
}

export function BriefTabs({ currentRole }: { currentRole: string }) {
  return (
    <div className="brief-tabs">
      {ROLES.map((r) => (
        <a
          key={r.key}
          href={`/briefs?role=${r.key}`}
          className={`brief-tab ${currentRole === r.key ? "active" : ""}`}
        >
          {r.label}
        </a>
      ))}
    </div>
  );
}
