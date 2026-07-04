"use client";

import { useMemo, useState } from "react";
import {
  DndContext,
  type DragEndEvent,
  DragOverlay,
  type DragStartEvent,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/auth";
import type { KanbanBoard as KanbanBoardType, TaskListItem } from "@/lib/kanban";
import KanbanColumn from "./KanbanColumn";
import KanbanTaskCard from "./KanbanTaskCard";
import CreateTaskModal from "./CreateTaskModal";
import TaskDetail from "./TaskDetail";

interface KanbanBoardProps {
  initialBoard: KanbanBoardType;
  currentUserId: string;
}

function findTaskInBoard(board: KanbanBoardType, taskId: number): TaskListItem | undefined {
  for (const column of board.columns) {
    for (const swimlane of column.swimlanes) {
      const task = swimlane.tasks.find((t) => t.task_id === taskId);
      if (task) return task;
    }
  }
  return undefined;
}

function findTaskStatus(board: KanbanBoardType, taskId: number): string | null {
  for (const column of board.columns) {
    for (const swimlane of column.swimlanes) {
      if (swimlane.tasks.some((t) => t.task_id === taskId)) {
        return column.status_key;
      }
    }
  }
  return null;
}

export default function KanbanBoard({ initialBoard, currentUserId }: KanbanBoardProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [board, setBoard] = useState<KanbanBoardType>(initialBoard);
  const [loading, setLoading] = useState(false);
  const [activeTask, setActiveTask] = useState<TaskListItem | null>(null);
  const [detailTaskId, setDetailTaskId] = useState<number | null>(null);
  const [createStatus, setCreateStatus] = useState<string | null>(() => {
    return searchParams.get("create") === "true" ? "todo" : null;
  });
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    for (const col of initialBoard.columns) {
      if (col.is_hidden) initial[col.status_key] = true;
    }
    return initial;
  });

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor)
  );

  const flatTasks = useMemo(() => {
    const tasks: TaskListItem[] = [];
    for (const column of board.columns) {
      for (const swimlane of column.swimlanes) {
        tasks.push(...swimlane.tasks);
      }
    }
    return tasks;
  }, [board]);

  async function loadBoard() {
    setLoading(true);
    const result = await apiFetch<KanbanBoardType>("/api/kanban/personal");
    setLoading(false);
    if (result.ok) {
      setBoard(result.data);
    }
  }

  function handleDragStart(event: DragStartEvent) {
    const id = event.active.id.toString();
    if (id.startsWith("task-")) {
      const taskId = parseInt(id.replace("task-", ""), 10);
      const task = findTaskInBoard(board, taskId);
      if (task) setActiveTask(task);
    }
  }

  async function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    setActiveTask(null);

    if (!over) return;

    const activeId = active.id.toString();
    if (!activeId.startsWith("task-")) return;
    const taskId = parseInt(activeId.replace("task-", ""), 10);

    const currentStatus = findTaskStatus(board, taskId);
    if (!currentStatus) return;

    const overId = over.id.toString();
    let targetStatus: string | null = null;
    if (overId.startsWith("column-")) {
      targetStatus = overId.replace("column-", "");
    } else if (overId.startsWith("task-")) {
      targetStatus = findTaskStatus(board, parseInt(overId.replace("task-", ""), 10));
    }

    if (!targetStatus || targetStatus === currentStatus) return;

    const result = await apiFetch(`/api/tasks/${taskId}/drag`, {
      method: "PUT",
      body: JSON.stringify({ status: targetStatus }),
    });

    if (result.ok) {
      await loadBoard();
    }
  }

  function toggleColumn(statusKey: string) {
    setCollapsed((prev) => ({ ...prev, [statusKey]: !prev[statusKey] }));
  }

  function closeCreateModal() {
    setCreateStatus(null);
    if (searchParams.get("create") === "true") {
      router.replace("/kanban");
    }
  }

  return (
    <div className="kanban-board-wrapper">
      <div className="topbar">
        <div className="flex items-center gap-8">
          <h2>个人 Kanban</h2>
          {loading && <span className="text-3">刷新中...</span>}
        </div>
        <div className="flex items-center gap-12">
          <button
            type="button"
            className="btn"
            onClick={() => router.push("/kanban/config")}
          >
            配置 Kanban
          </button>
        </div>
      </div>

      <DndContext
        sensors={sensors}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="kanban-board">
          {board.columns.map((column) => {
            const tasks: TaskListItem[] = [];
            for (const swimlane of column.swimlanes) {
              tasks.push(...swimlane.tasks);
            }
            return (
              <KanbanColumn
                key={column.status_key}
                column={column}
                tasks={tasks}
                onOpenDetail={setDetailTaskId}
                onOpenCreate={setCreateStatus}
                isCollapsed={collapsed[column.status_key]}
                onToggleCollapse={() => toggleColumn(column.status_key)}
              />
            );
          })}
        </div>
        <DragOverlay>
          {activeTask ? <KanbanTaskCard task={activeTask} onOpenDetail={() => {}} /> : null}
        </DragOverlay>
      </DndContext>

      <CreateTaskModal
        isOpen={createStatus !== null}
        onClose={closeCreateModal}
        initialStatus={createStatus}
        onCreated={loadBoard}
      />

      {detailTaskId !== null && (
        <TaskDetail
          taskId={detailTaskId}
          currentUserId={currentUserId}
          onClose={() => setDetailTaskId(null)}
          onDeleted={loadBoard}
        />
      )}
    </div>
  );
}
