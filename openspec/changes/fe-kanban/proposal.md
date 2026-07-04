## Why

The backend Task & Kanban APIs are ready, but the web frontend still has no way for users to view a personal kanban board, manage tasks, or configure board columns. We need a set of kanban-related UI pages so users can execute work tracked in BriefChain.

## What Changes

- Add a **个人 kanban** page that renders columns and task cards from `/api/v1/kanban/personal`.
- Add a **kanban 配置页** for choosing templates, setting swimlanes / done-visible-days, and editing column names/colors.
- Add a **Task 详情页/弹层** to view and edit task fields, sub-tasks, and comments.
- Add a **创建 Task** modal triggered from the sidebar and from kanban column headers.
- Update the **左侧边栏** to add "创建 Task" and "个人 kanban" navigation entries.
- Add internal Next.js API route handlers under `web/app/api/` to proxy task/kanban requests with the session cookie.

## Capabilities

### New Capabilities

- `fe-kanban-board`: Personal kanban board page. Loads board data, renders columns and task cards, handles hidden-column folding, overdue highlighting, and navigation to task detail / config.
- `fe-kanban-config`: Kanban configuration page. Select template, set group / done-visible-days, edit column names/colors, save (with optional "save as public template"), and fork handling is transparent via backend.
- `fe-task-detail`: Task detail view (modal or slide-over). Shows task info, allows editable fields for creator/assignee, lists sub-tasks and comments, supports comment CRUD and task deletion.
- `fe-task-create`: Create-task modal. Supports creating `task`, `bug`, or `sub_task` with validation (e.g., `sub_task` requires parent), and can be opened from sidebar or column header.
- `fe-sidebar-kanban-entry`: Sidebar updates to expose "创建 Task" and "个人 kanban" navigation.

### Modified Capabilities

- None. This is a pure frontend addition; existing brief pages are unaffected.

## Impact

- New Next.js pages: `web/app/kanban/page.tsx`, `web/app/kanban/config/page.tsx`, `web/app/tasks/[task_id]/page.tsx` (or modal route).
- New client components: `KanbanBoard`, `KanbanColumn`, `KanbanTaskCard`, `TaskDetail`, `CreateTaskModal`, `KanbanConfigForm`.
- New internal API routes: `web/app/api/kanban/**`, `web/app/api/tasks/**`.
- Updated `Sidebar.tsx` and `globals.css` for kanban-specific styles.
- Depends on the `be-kanban` backend APIs being available.
