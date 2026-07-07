"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, isNonEmpty } from "@/lib/auth";
import { localDateToEndOfDayISO } from "@/lib/date";
import { BRIEF_TYPE_LABELS, type BriefType } from "@/lib/brief-types";

export default function NewBriefForm({ parentId }: { parentId?: string }) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [type, setType] = useState<BriefType>("idea");
  const [content, setContent] = useState("");
  const [priority, setPriority] = useState("p2");
  const [estimatedManDays, setEstimatedManDays] = useState("");
  const [expectedCompletionAt, setExpectedCompletionAt] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const validate = (): boolean => {
    if (!isNonEmpty(title)) {
      setError("标题不能为空");
      return false;
    }
    if (!isNonEmpty(content)) {
      setError("内容不能为空");
      return false;
    }
    setError(null);
    return true;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!validate()) return;

    setLoading(true);
    const result = await apiFetch<{ brief_id: string }>("/api/briefs", {
      method: "POST",
      body: JSON.stringify({
        title: title.trim(),
        type,
        content: content.trim(),
        priority,
        estimated_man_days: estimatedManDays ? parseFloat(estimatedManDays) : null,
        expected_completion_at: expectedCompletionAt
          ? localDateToEndOfDayISO(expectedCompletionAt)
          : null,
        parent_id: parentId ?? null,
        attachments: [],
      }),
    });
    setLoading(false);

    if (!result.ok) {
      setError(result.message);
      return;
    }
    router.replace(`/briefs/${result.data.brief_id}`);
  };

  return (
    <div className="card" style={{ maxWidth: 720 }}>
      {error && <div className="error-message mb-16">{error}</div>}
      {parentId && (
        <div className="mb-16 text-2" style={{ fontSize: 12 }}>
          正在为父 Brief 创建子 Brief
        </div>
      )}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="title" className="form-label">标题</label>
          <input
            id="title"
            type="text"
            placeholder="Brief 标题"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="type" className="form-label">类型</label>
          <select
            id="type"
            value={type}
            onChange={(e) => setType(e.target.value as BriefType)}
            disabled={loading}
          >
            <option value="idea">{BRIEF_TYPE_LABELS.idea}</option>
            <option value="epic">{BRIEF_TYPE_LABELS.epic}</option>
            <option value="feature">{BRIEF_TYPE_LABELS.feature}</option>
            <option value="story">{BRIEF_TYPE_LABELS.story}</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="content" className="form-label">内容</label>
          <textarea
            id="content"
            placeholder="描述需求背景、验收标准、预估等信息..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
            disabled={loading}
            rows={10}
          />
        </div>

        <div className="form-group">
          <label htmlFor="priority" className="form-label">优先级</label>
          <select
            id="priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            disabled={loading}
          >
            <option value="p0">P0</option>
            <option value="p1">P1</option>
            <option value="p2">P2</option>
            <option value="p3">P3</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="estimated_man_days" className="form-label">预估人天</label>
          <input
            id="estimated_man_days"
            type="number"
            min="0"
            step="0.5"
            placeholder="例如：3"
            value={estimatedManDays}
            onChange={(e) => setEstimatedManDays(e.target.value)}
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="expected_completion_at" className="form-label">预期完成时间</label>
          <input
            id="expected_completion_at"
            type="date"
            value={expectedCompletionAt}
            onChange={(e) => setExpectedCompletionAt(e.target.value)}
            disabled={loading}
          />
        </div>

        <div className="flex gap-8">
          <button
            type="button"
            className="btn"
            onClick={() => router.back()}
            disabled={loading}
          >
            取消
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "创建中..." : "创建"}
          </button>
        </div>
      </form>
    </div>
  );
}
