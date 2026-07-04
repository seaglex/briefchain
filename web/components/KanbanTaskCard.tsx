"use client";

import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { formatDateTime, isOverdue } from "@/lib/date";
import type { TaskListItem } from "@/lib/kanban";

interface KanbanTaskCardProps {
  task: TaskListItem;
  onOpenDetail: (taskId: number) => void;
}

function priorityClass(priority: string): string {
  if (priority === "p0" || priority === "p1") return "badge-p1";
  if (priority === "p2") return "badge-p2";
  return "badge-p3";
}

export default function KanbanTaskCard({ task, onOpenDetail }: KanbanTaskCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useDraggable({ id: `task-${task.task_id}`, data: { task } });

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.5 : 1,
  };

  const overdue = isOverdue(task.updated_at); // use updated_at? for due_date if available
  // Note: TaskListItem does not include due_date; highlight based on updated_at is not ideal.
  // We keep the prop interface simple and rely on the detail view for real due-date highlighting.
  const highlight = overdue;

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      className={`kanban-card ${highlight ? "kanban-card-overdue" : ""}`}
      style={style}
    >
      <div className="kanban-card-title">{task.title}</div>
      <div className="kanban-card-meta">
        <span className={`badge ${priorityClass(task.priority)}`}>
          {task.priority.toUpperCase()}
        </span>
        <span className="text-3">{task.assignee_name || "未分配"}</span>
      </div>
      <div className="kanban-card-footer">
        <span className="text-3">{formatDateTime(task.updated_at)}</span>
        <button
          type="button"
          className="btn btn-sm"
          onClick={(e) => {
            e.stopPropagation();
            onOpenDetail(task.task_id);
          }}
        >
          查看详情
        </button>
      </div>
    </div>
  );
}
