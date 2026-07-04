## 1. Internal API routes

- [x] 1.1 Create `web/app/api/kanban/personal/route.ts` to proxy `GET /api/v1/kanban/personal`
- [x] 1.2 Create `web/app/api/kanbans/route.ts` to proxy `POST /api/v1/kanbans`
- [x] 1.3 Create `web/app/api/kanbans/[id]/route.ts` to proxy `GET`/`PUT /api/v1/kanbans/:id`
- [x] 1.4 Create `web/app/api/kanbans/[id]/columns/route.ts` to proxy `PUT /api/v1/kanbans/:id/columns`
- [x] 1.5 Create `web/app/api/kanban-templates/route.ts` to proxy `GET /api/v1/kanban-templates`
- [x] 1.6 Create `web/app/api/tasks/route.ts` to proxy `POST /api/v1/tasks`
- [x] 1.7 Create `web/app/api/tasks/[id]/route.ts` to proxy `GET`/`PUT`/`DELETE /api/v1/tasks/:id`
- [x] 1.8 Create `web/app/api/tasks/[id]/drag/route.ts` to proxy `PUT /api/v1/tasks/:id/drag`
- [x] 1.9 Create `web/app/api/tasks/[id]/comments/route.ts` to proxy `GET`/`POST /api/v1/tasks/:id/comments`
- [x] 1.10 Create `web/app/api/comments/[id]/route.ts` to proxy `PUT`/`DELETE /api/v1/comments/:id`

## 2. Shared types and helpers

- [x] 2.1 Add TypeScript types for board, task, kanban config, template, and comments in `web/lib/kanban.ts`
- [x] 2.2 Add utility to format due dates and detect overdue tasks in `web/lib/date.ts`
- [x] 2.3 Install `@dnd-kit/core`, `@dnd-kit/sortable`, and `@dnd-kit/utilities` in the web app
- [x] 2.4 Add a client-only `DndContext` wrapper with pointer and keyboard sensors for the kanban board

## 3. Kanban board page and components

- [x] 3.1 Create `web/app/kanban/page.tsx` server component that fetches board data
- [x] 3.2 Create `web/components/KanbanBoard.tsx` client component rendering columns
- [x] 3.3 Create `web/components/KanbanColumn.tsx` with header color, task count, and "新建" button
- [x] 3.4 Create `web/components/KanbanTaskCard.tsx` showing title, priority, assignee, due date, and overdue highlight
- [x] 3.5 Implement hidden-column folding UI (collapsed width ~20%)
- [x] 3.6 Add "查看详情" action on cards and config button in board header
- [x] 3.7 Implement drag-and-drop with `@dnd-kit/core` + `@dnd-kit/sortable`; on drop in a different column call `PUT /api/tasks/:id/drag` and refresh the board

## 4. Kanban config page

- [x] 4.1 Create `web/app/kanban/config/page.tsx` client page
- [x] 4.2 Create `web/components/KanbanConfigForm.tsx` loading current config and templates
- [x] 4.3 Implement template selector with `GET /api/kanban-templates`
- [x] 4.4 Implement group and done-visible-days controls
- [x] 4.5 Implement editable column list (name, color) preserving status_key/position
- [x] 4.6 Implement "保存为公开模板" option with template name input
- [x] 4.7 Wire save to `PUT /api/kanbans/:id` and `PUT /api/kanbans/:id/columns`

## 5. Task detail modal

- [x] 5.1 Create `web/components/TaskDetail.tsx` modal component
- [x] 5.2 Fetch task detail (`GET /api/tasks/:id`) and display all fields
- [x] 5.3 Implement editable fields for creator/assignee with `PUT /api/tasks/:id`
- [x] 5.4 Implement delete task action for creator
- [x] 5.5 Render sub-tasks list with links to open their detail
- [x] 5.6 Render comments and implement comment CRUD

## 6. Create-task modal

- [x] 6.1 Create `web/components/CreateTaskModal.tsx` client component
- [x] 6.2 Implement type selector (task/bug/sub_task) with parent task input for sub_task
- [x] 6.3 Implement optional fields: brief, title, content, priority, assignee, estimated hours, due date
- [x] 6.4 Pre-fill status when opened from a column header
- [x] 6.5 Wire submit to `POST /api/tasks`

## 7. Sidebar and layout updates

- [x] 7.1 Update `web/components/Sidebar.tsx` to add "创建 Task" and "个人 kanban" entries
- [x] 7.2 Implement active state for `/kanban` and `/kanban/config`
- [x] 7.3 Wire "创建 Task" to open the create-task modal

## 8. Styles and verification

- [x] 8.1 Add kanban-specific CSS classes to `web/app/globals.css` (board grid, column, card, hidden column)
- [x] 8.2 Run `next build` or type-check for the web app
- [x] 8.3 Smoke test board, config, task create, and task detail flows against the backend
