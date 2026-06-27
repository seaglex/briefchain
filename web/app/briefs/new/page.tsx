"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, isNonEmpty } from "@/lib/auth";
import Sidebar from "@/components/Sidebar";

export default function NewBriefPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
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
        content: content.trim(),
        priority,
        estimated_man_days: estimatedManDays ? parseFloat(estimatedManDays) : null,
        expected_completion_at: expectedCompletionAt
          ? new Date(expectedCompletionAt).toISOString()
          : null,
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
    <div className="app">
      <Sidebar />
      <div className="main" style={{ flex: 1 }}>
        <div className="topbar">
          <div className="flex items-center gap-8">
            <h2>创建 Brief</h2>
          </div>
        </div>

        <div className="content">
          <div className="card" style={{ maxWidth: 720 }}>
            {error && <div className="error-message mb-16">{error}</div>}
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
                  type="datetime-local"
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
        </div>
      </div>
    </div>
  );
}
