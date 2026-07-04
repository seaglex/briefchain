"use client";

import { useDroppable } from "@dnd-kit/core";
import type { KanbanColumn as KanbanColumnType, TaskListItem } from "@/lib/kanban";
import KanbanTaskCard from "./KanbanTaskCard";

interface KanbanColumnProps {
  column: KanbanColumnType;
  tasks: TaskListItem[];
  onOpenDetail: (taskId: number) => void;
  onOpenCreate: (status: string) => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export default function KanbanColumn({
  column,
  tasks,
  onOpenDetail,
  onOpenCreate,
  isCollapsed,
  onToggleCollapse,
}: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: `column-${column.status_key}`,
    data: { status: column.status_key },
  });

  const headerStyle: React.CSSProperties = {
    backgroundColor: column.color || "var(--c-bg-3)",
    color: "#fff",
  };

  if (isCollapsed) {
    return (
      <div
        ref={setNodeRef}
        className={`kanban-column kanban-column-collapsed ${isOver ? "kanban-column-over" : ""}`}
      >
        <div
          className="kanban-column-header kanban-column-header-collapsed"
          style={headerStyle}
          onClick={onToggleCollapse}
          role="button"
          tabIndex={0}
        >
          <div className="kanban-column-name">{column.name}</div>
          <div className="kanban-column-count">{tasks.length}</div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={setNodeRef}
      className={`kanban-column ${isOver ? "kanban-column-over" : ""}`}
    >
      <div className="kanban-column-header" style={headerStyle}>
        <div className="kanban-column-title">
          <span className="kanban-column-name">{column.name}</span>
          <span className="kanban-column-count">{tasks.length}</span>
        </div>
        <div className="kanban-column-actions">
          <button
            type="button"
            className="btn btn-sm"
            onClick={() => onOpenCreate(column.status_key)}
          >
            新建
          </button>
          {column.is_hidden && (
            <button
              type="button"
              className="btn btn-sm"
              onClick={onToggleCollapse}
            >
              折叠
            </button>
          )}
        </div>
      </div>
      <div className="kanban-column-body">
        {tasks.map((task) => (
          <KanbanTaskCard
            key={task.task_id}
            task={task}
            onOpenDetail={onOpenDetail}
          />
        ))}
        {tasks.length === 0 && (
          <div className="kanban-column-empty">暂无任务</div>
        )}
      </div>
    </div>
  );
}
