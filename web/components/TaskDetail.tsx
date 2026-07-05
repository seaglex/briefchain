"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch, isNonEmpty } from "@/lib/auth";
import { formatDateTime, isoToLocalDateTime, isOverdue, localDateTimeToISO } from "@/lib/date";
import type { TaskComment, TaskDetailResponse } from "@/lib/kanban";
import UserSelector from "./UserSelector";
import CreateTaskModal from "./CreateTaskModal";

interface TaskDetailProps {
  taskId: number;
  currentUserId: string;
}

function priorityClass(priority: string): string {
  if (priority === "p0" || priority === "p1") return "badge-p1";
  if (priority === "p2") return "badge-p2";
  return "badge-p3";
}

export default function TaskDetail({ taskId, currentUserId }: TaskDetailProps) {
  const router = useRouter();
  const [data, setData] = useState<TaskDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCreateSubtaskOpen, setIsCreateSubtaskOpen] = useState(false);

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [status, setStatus] = useState("todo");
  const [priority, setPriority] = useState("p2");
  const [assigneeId, setAssigneeId] = useState<string | null>(null);
  const [estimatedHours, setEstimatedHours] = useState("");
  const [actualHours, setActualHours] = useState("");
  const [dueDate, setDueDate] = useState("");

  const [commentContent, setCommentContent] = useState("");
  const [editingCommentId, setEditingCommentId] = useState<number | null>(null);
  const [editingContent, setEditingContent] = useState("");

  async function loadDetail() {
    setLoading(true);
    const result = await apiFetch<TaskDetailResponse>(`/api/tasks/${taskId}`);
    setLoading(false);
    if (!result.ok) {
      setError(result.message);
      return;
    }
    setData(result.data);
    const t = result.data.task;
    setTitle(t.title);
    setContent(t.content || "");
    setStatus(t.status);
    setPriority(t.priority);
    setAssigneeId(t.assignee_id);
    setEstimatedHours(t.estimated_hours?.toString() || "");
    setActualHours(t.actual_hours?.toString() || "");
    setDueDate(isoToLocalDateTime(t.due_date));
    setError(null);
  }

  useEffect(() => {
    loadDetail();
  }, [taskId]);

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    if (!isNonEmpty(title)) {
      setError("标题不能为空");
      return;
    }
    setSaving(true);
    const result = await apiFetch(`/api/tasks/${taskId}`, {
      method: "PUT",
      body: JSON.stringify({
        title: title.trim(),
        content: content.trim() || null,
        status,
        priority,
        assignee_id: assigneeId,
        estimated_hours: estimatedHours ? parseInt(estimatedHours, 10) : null,
        actual_hours: actualHours ? parseInt(actualHours, 10) : null,
        due_date: dueDate ? localDateTimeToISO(dueDate) : null,
      }),
    });
    setSaving(false);
    if (!result.ok) {
      setError(result.message);
      return;
    }
    await loadDetail();
  }

  async function handleDelete() {
    if (!confirm("确定删除该 Task？")) return;
    const result = await apiFetch(`/api/tasks/${taskId}`, { method: "DELETE" });
    if (!result.ok) {
      setError(result.message);
      return;
    }
    router.push("/kanban");
  }

  async function handleAddComment(event: React.FormEvent) {
    event.preventDefault();
    if (!isNonEmpty(commentContent)) return;
    const result = await apiFetch(`/api/tasks/${taskId}/comments`, {
      method: "POST",
      body: JSON.stringify({ content: commentContent.trim() }),
    });
    if (!result.ok) {
      setError(result.message);
      return;
    }
    setCommentContent("");
    await loadDetail();
  }

  async function handleUpdateComment(commentId: number) {
    if (!isNonEmpty(editingContent)) return;
    const result = await apiFetch(`/api/comments/${commentId}`, {
      method: "PUT",
      body: JSON.stringify({ content: editingContent.trim() }),
    });
    if (!result.ok) {
      setError(result.message);
      return;
    }
    setEditingCommentId(null);
    setEditingContent("");
    await loadDetail();
  }

  async function handleDeleteComment(commentId: number) {
    if (!confirm("确定删除该评论？")) return;
    const result = await apiFetch(`/api/comments/${commentId}`, { method: "DELETE" });
    if (!result.ok) {
      setError(result.message);
      return;
    }
    await loadDetail();
  }

  if (loading && !data) {
    return <div className="content">加载中...</div>;
  }

  if (!data) {
    return (
      <div className="content">
        {error && <div className="error-message mb-16">{error}</div>}
      </div>
    );
  }

  const task = data.task;
  const isCreator = task.created_by === currentUserId;
  const isAssignee = task.assignee_id === currentUserId;
  const canEdit = isCreator || isAssignee;

  return (
    <div className="content">
      <div className="flex items-center justify-between mb-16">
        <div className="flex items-center gap-8">
          <h2>{task.title}
          {task.brief_id && (
            <Link
              href={`/briefs/${task.brief_id}`}
              className="badge badge-reviewed version-link"
            >
              关联 Brief
            </Link>
          )}
          </h2>
        </div>
        <div className="flex items-center gap-16">
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => setIsCreateSubtaskOpen(true)}
            disabled={saving}
          >
            创建子任务
          </button>
          {canEdit && (
            <button type="submit" form="task-form" className="btn btn-primary btn-sm" disabled={saving}>
              {saving ? "保存中..." : "保存"}
            </button>
          )}
          {isCreator && (
            <button type="button" className="btn btn-danger btn-sm" onClick={handleDelete} disabled={saving}>
              删除
            </button>
          )}
        </div>
      </div>

      {error && <div className="error-message mb-16">{error}</div>}

      <form id="task-form" onSubmit={handleSave}>
        <div className="form-group">
          <label className="form-label">标题</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} disabled={!canEdit || saving} />
        </div>
        <div className="form-group">
          <label className="form-label">内容</label>
          <textarea value={content} onChange={(e) => setContent(e.target.value)} disabled={!canEdit || saving} rows={4} />
        </div>
        <div className="form-group">
          <label className="form-label">状态</label>
          <select value={status} onChange={(e) => setStatus(e.target.value)} disabled={!canEdit || saving}>
            <option value="todo">待办</option>
            <option value="in_progress">进行中</option>
            <option value="in_review">审阅中</option>
            <option value="done">已完成</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">优先级</label>
          <select value={priority} onChange={(e) => setPriority(e.target.value)} disabled={!canEdit || saving}>
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
          <label className="form-label">预估工时</label>
          <input type="number" min="0" value={estimatedHours} onChange={(e) => setEstimatedHours(e.target.value)} disabled={!canEdit || saving} />
        </div>
        <div className="form-group">
          <label className="form-label">实际工时</label>
          <input type="number" min="0" value={actualHours} onChange={(e) => setActualHours(e.target.value)} disabled={!canEdit || saving} />
        </div>
        <div className="form-group">
          <label className="form-label">截止日期</label>
          <input type="datetime-local" value={dueDate} onChange={(e) => setDueDate(e.target.value)} disabled={!canEdit || saving} />
          {isOverdue(task.due_date) && <span className="error-message">已超时</span>}
        </div>
      </form>

      <div className="mb-24">
        <h3 className="mb-12">子任务</h3>
        {data.sub_tasks.length === 0 && <div className="text-3">暂无子任务</div>}
        {data.sub_tasks.map((sub) => (
          <div key={sub.task_id} className="card mb-8">
            <span className={`badge ${priorityClass(sub.priority)}`}>{sub.priority.toUpperCase()}</span>
            <Link href={`/tasks/${sub.task_id}`} className="ml-8">
              {sub.title}
            </Link>
          </div>
        ))}
      </div>

      <div>
        <h3 className="mb-12">评论</h3>
        <form onSubmit={handleAddComment} className="form-group">
          <textarea
            value={commentContent}
            onChange={(e) => setCommentContent(e.target.value)}
            placeholder="添加评论..."
            rows={2}
          />
          <button type="submit" className="btn btn-primary btn-sm mt-8">发表评论</button>
        </form>
        <div className="mt-16">
          {data.comments.map((comment) => (
            <CommentItem
              key={comment.id}
              comment={comment}
              currentUserId={currentUserId}
              isEditing={editingCommentId === comment.id}
              editingContent={editingContent}
              setEditingContent={setEditingContent}
              onStartEdit={() => {
                setEditingCommentId(comment.id);
                setEditingContent(comment.content);
              }}
              onCancelEdit={() => setEditingCommentId(null)}
              onUpdate={() => handleUpdateComment(comment.id)}
              onDelete={() => handleDeleteComment(comment.id)}
            />
          ))}
        </div>
      </div>

      <CreateTaskModal
        isOpen={isCreateSubtaskOpen}
        onClose={() => setIsCreateSubtaskOpen(false)}
        initialStatus={task.status}
        parentTaskId={task.task_id}
        briefId={task.brief_id}
        teamId={task.team_id}
        onCreated={() => {
          setIsCreateSubtaskOpen(false);
          loadDetail();
        }}
      />
    </div>
  );
}

interface CommentItemProps {
  comment: TaskComment;
  currentUserId: string;
  isEditing: boolean;
  editingContent: string;
  setEditingContent: (value: string) => void;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onUpdate: () => void;
  onDelete: () => void;
}

function CommentItem({
  comment,
  currentUserId,
  isEditing,
  editingContent,
  setEditingContent,
  onStartEdit,
  onCancelEdit,
  onUpdate,
  onDelete,
}: CommentItemProps) {
  const isOwner = comment.created_by === currentUserId;
  return (
    <div className="comment-item">
      <div className="comment-meta">
        <span className="font-medium">{comment.created_by_name}</span>
        <span className="text-3">{formatDateTime(comment.created_at)}</span>
      </div>
      {isEditing ? (
        <div className="form-group">
          <textarea value={editingContent} onChange={(e) => setEditingContent(e.target.value)} rows={2} />
          <div className="flex gap-8 mt-8">
            <button className="btn btn-primary btn-sm" onClick={onUpdate}>保存</button>
            <button className="btn btn-sm" onClick={onCancelEdit}>取消</button>
          </div>
        </div>
      ) : (
        <div className="comment-content">{comment.content}</div>
      )}
      {isOwner && !isEditing && (
        <div className="flex gap-8 mt-8">
          <button className="btn btn-sm" onClick={onStartEdit}>编辑</button>
          <button className="btn btn-sm btn-danger" onClick={onDelete}>删除</button>
        </div>
      )}
    </div>
  );
}
