"use client";

import { useEffect, useState } from "react";
import { apiFetch, isNonEmpty } from "@/lib/auth";
import { isoToLocalDateTime, localDateTimeToISO } from "@/lib/date";
import UserSelector from "./UserSelector";

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialStatus?: string | null;
  parentTaskId?: number | null;
  briefId?: string | null;
  teamId?: string | null;
  onCreated?: () => void;
}

export default function CreateTaskModal({
  isOpen,
  onClose,
  initialStatus,
  parentTaskId,
  briefId,
  teamId,
  onCreated,
}: CreateTaskModalProps) {
  const [type, setType] = useState<"task" | "bug" | "sub_task">("task");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [status, setStatus] = useState(initialStatus || "todo");
  const [priority, setPriority] = useState("p2");
  const [assigneeId, setAssigneeId] = useState<string | null>(null);
  const [estimatedHours, setEstimatedHours] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setType(parentTaskId ? "sub_task" : "task");
      setTitle("");
      setContent("");
      setStatus(initialStatus || "todo");
      setPriority("p2");
      setAssigneeId(null);
      setEstimatedHours("");
      setDueDate("");
      setError(null);
    }
  }, [isOpen, initialStatus, parentTaskId]);

  if (!isOpen) return null;

  const validate = (): boolean => {
    if (!isNonEmpty(title)) {
      setError("标题不能为空");
      return false;
    }
    if (type === "sub_task" && !parentTaskId) {
      setError("子任务必须关联父任务");
      return false;
    }
    setError(null);
    return true;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!validate()) return;

    setLoading(true);
    const result = await apiFetch<{ task_id: number }>("/api/tasks", {
      method: "POST",
      body: JSON.stringify({
        type,
        parent_task_id: type === "sub_task" ? parentTaskId : null,
        brief_id: briefId ?? null,
        team_id: teamId ?? null,
        title: title.trim(),
        content: content.trim() || null,
        status,
        priority,
        assignee_id: assigneeId,
        estimated_hours: estimatedHours ? parseInt(estimatedHours, 10) : null,
        due_date: dueDate ? localDateTimeToISO(dueDate) : null,
      }),
    });
    setLoading(false);

    if (!result.ok) {
      setError(result.message);
      return;
    }

    onCreated?.();
    onClose();
  };

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <div className="modal-header">
          <h3>创建 Task</h3>
          <button type="button" className="btn btn-sm" onClick={onClose} disabled={loading}>
            关闭
          </button>
        </div>
        <div className="modal-body">
          {error && <div className="error-message mb-16">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">类型</label>
              {parentTaskId ? (
                <select value="sub_task" disabled>
                  <option value="sub_task">Sub-task</option>
                </select>
              ) : (
                <select value={type} onChange={(e) => setType(e.target.value as typeof type)} disabled={loading}>
                  <option value="task">Task</option>
                  <option value="bug">Bug</option>
                </select>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">标题</label>
              <input value={title} onChange={(e) => setTitle(e.target.value)} disabled={loading} />
            </div>

            <div className="form-group">
              <label className="form-label">内容</label>
              <textarea value={content} onChange={(e) => setContent(e.target.value)} disabled={loading} rows={4} />
            </div>

            <div className="form-group">
              <label className="form-label">状态</label>
              <select value={status} onChange={(e) => setStatus(e.target.value)} disabled={loading}>
                <option value="todo">待办</option>
                <option value="in_progress">进行中</option>
                <option value="in_review">审阅中</option>
                <option value="done">已完成</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">优先级</label>
              <select value={priority} onChange={(e) => setPriority(e.target.value)} disabled={loading}>
                <option value="p0">P0</option>
                <option value="p1">P1</option>
                <option value="p2">P2</option>
                <option value="p3">P3</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">执行人</label>
              <UserSelector selectedUserId={assigneeId} onSelect={setAssigneeId} />
            </div>

            <div className="form-group">
              <label className="form-label">预估工时（小时）</label>
              <input
                type="number"
                min="0"
                value={estimatedHours}
                onChange={(e) => setEstimatedHours(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="form-label">截止日期</label>
              <input
                type="datetime-local"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="flex gap-8">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? "创建中..." : "创建"}
              </button>
              <button type="button" className="btn" onClick={onClose} disabled={loading}>取消</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
