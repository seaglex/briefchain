"use client";

import { useRouter, useSearchParams } from "next/navigation";

const ROLES = [
  { key: "assigned", label: "分配给我" },
  { key: "created", label: "我创建的" },
  { key: "pending", label: "待处理" },
];

const UPSTREAM_STATES = [
  { key: "", label: "全部上游状态" },
  { key: "editing", label: "editing" },
  { key: "reviewed", label: "reviewed" },
  { key: "sent", label: "sent" },
  { key: "in_process", label: "in_process" },
  { key: "suspended", label: "suspended" },
  { key: "cancelled", label: "cancelled" },
  { key: "done", label: "done" },
];

const DOWNSTREAM_STATES = [
  { key: "", label: "全部下游状态" },
  { key: "opened", label: "opened" },
  { key: "submitted", label: "submitted" },
  { key: "delegated", label: "delegated" },
  { key: "blocked", label: "blocked" },
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
  const upstreamState = searchParams.get("upstream_state") || "";
  const downstreamState = searchParams.get("downstream_state") || "";
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
        value={upstreamState}
        onChange={(e) => updateParam("upstream_state", e.target.value)}
      >
        {UPSTREAM_STATES.map((s) => (
          <option key={s.key} value={s.key}>{s.label}</option>
        ))}
      </select>

      <select
        className="filter-select"
        value={downstreamState}
        onChange={(e) => updateParam("downstream_state", e.target.value)}
      >
        {DOWNSTREAM_STATES.map((s) => (
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
