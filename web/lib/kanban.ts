/**
 * TypeScript types for the kanban frontend.
 *
 * These mirror the backend response shapes documented in
 * docs/mvp_design/07-task-kanban-api-design.md.
 */

export interface KanbanSummary {
  kanban_id: number;
  kanban_template_id: number;
  kanban_template_mode: "simple" | "customized";
  group: "none" | "assignee" | "brief" | "priority";
  done_visible_days: number;
  is_default: boolean;
}

export interface KanbanColumn {
  column_id: number;
  status_key: string;
  name: string;
  color: string | null;
  is_hidden: boolean;
  position: number;
  swimlanes: KanbanSwimlane[];
}

export interface KanbanSwimlane {
  swimlane_key: string | null;
  tasks: TaskListItem[];
}

export interface KanbanBoard {
  kanban: KanbanSummary;
  columns: KanbanColumn[];
}

export interface TaskListItem {
  task_id: number;
  type: "task" | "bug" | "sub_task";
  title: string;
  status: string;
  priority: "p0" | "p1" | "p2" | "p3";
  assignee_id: string | null;
  assignee_name: string | null;
  brief_id: string | null;
  updated_at: string;
}

export interface TaskDetail extends TaskListItem {
  parent_task_id: number | null;
  team_id: string | null;
  content: string | null;
  estimated_hours: number | null;
  actual_hours: number | null;
  due_date: string | null;
  status_changed_by: string | null;
  status_changed_at: string | null;
  created_by: string;
  created_by_name: string;
  created_at: string;
  is_deleted: boolean;
  deleted_by: string | null;
  deleted_at: string | null;
}

export interface TaskDetailResponse {
  task: TaskDetail;
  sub_tasks: TaskListItem[];
  comments: TaskComment[];
}

export interface TaskComment {
  id: number;
  content: string;
  created_by: string;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface KanbanConfig extends KanbanSummary {
  name: string;
  owner_type: "user" | "team";
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface KanbanTemplateSummary {
  kanban_template_id: number;
  name: string;
  kanban_template_mode: "simple" | "customized";
  created_by: string;
}

export interface KanbanConfigResponse {
  kanban: KanbanConfig;
  template: KanbanTemplateSummary;
  columns: KanbanColumnConfig[];
}

export interface KanbanColumnConfig {
  column_id: number;
  status_key: string;
  name: string;
  color: string | null;
  is_hidden: boolean;
  position: number;
}

export interface KanbanTemplateListItem extends KanbanTemplateSummary {
  created_by_name: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface KanbanTemplateListResponse {
  templates: KanbanTemplateListItem[];
  next_cursor: string | null;
}

export interface KanbanTemplateDetailResponse {
  template: KanbanTemplateListItem;
  columns: KanbanColumnConfig[];
}
