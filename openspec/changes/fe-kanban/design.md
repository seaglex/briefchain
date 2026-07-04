## Context

The `be-kanban` backend now exposes Task & Kanban REST APIs. The frontend currently only supports Brief workflows. We need to add kanban-oriented pages and components on top of the existing Next.js app (App Router, server components for data fetching, client components for interactivity).

Design references:
- `docs/mvp_design/06-task-kanban-design.md` — domain model and rules
- `docs/mvp_design/07-task-kanban-api-design.md` — backend endpoint contracts
- `docs/mvp_design/09-fe-kanban-design.md` — UI/UX requirements

Existing patterns in the repo: server components call `serverFetch` from `lib/server-auth.ts`; client components call internal Next.js API routes via `apiFetch` from `lib/auth.ts`; forms use controlled inputs and CSS classes from `globals.css`.

## Goals / Non-Goals

**Goals:**

- Render the personal kanban board (`/kanban/personal`) as a column-based view.
- Allow users to create tasks from the sidebar and from column headers.
- Allow drag-and-drop status changes using `@dnd-kit/core` + `@dnd-kit/sortable`.
- Provide a task detail view (modal or dedicated page) with editable fields and comments.
- Provide a kanban config page to switch templates, set group/done-visible-days, and edit column names/colors.
- Add sidebar navigation entries for "创建 Task" and "个人 kanban".

**Non-Goals:**

- Team kanban board.
- Swimlane UI rendering (backend supports it, frontend MVP uses `group=none`).
- Public template creation beyond the "save as public template" checkbox in config.
- Offline support or optimistic UI beyond basic loading states.

## Decisions

### 1. Use internal Next.js API routes to proxy kanban/task requests

Create `web/app/api/kanban/**` and `web/app/api/tasks/**` route handlers that mirror the backend endpoints and attach the session token via `proxyWithToken`. Client components will call these internal routes so authentication stays server-side and CORS is avoided.

**Rationale:** Matches the existing `web/app/api/briefs/route.ts` pattern and keeps client code free of token handling.

### 2. Server component for the board page, client components for columns/cards/modals

`web/app/kanban/page.tsx` will be a Server Component that fetches the board via `serverFetch`. It passes data to client components (`KanbanBoard`, `KanbanColumn`, `KanbanTaskCard`) for rendering and interactions. The config page can be a client page because it needs many local edits before saving.

**Rationale:** Aligns with current brief list page architecture; minimizes client-side JavaScript while keeping interactivity where needed.

### 3. Modal-based task detail and creation

Task detail and creation will open in a modal (or slide-over) rather than a dedicated page. This keeps the user in the kanban context.

**Rationale:** Matches the design doc's "弹窗方式或者弹层方式" guidance and avoids complex page-state management during board navigation.

### 4. Status change via drag-and-drop using @dnd-kit

Moving a task card to another column will be implemented with `@dnd-kit/core` + `@dnd-kit/sortable`. Dropping a card in a different column calls `PUT /api/tasks/:task_id/drag` with the target `status`. Sorting cards within the same column is allowed visually but only the status change is persisted in MVP (position is not stored).

**Rationale:** `@dnd-kit` is modern, modular, touch/keyboard accessible, and works with React 19 / Next.js App Router client components. It gives us full control over the kanban layout while reusing the backend drag endpoint.

### 5. Config page handles column edits locally until save

The config page will keep column edits in React state and send the full column list on save. The backend decides whether to fork the template.

**Rationale:** Simplifies the frontend; fork logic is intentionally delegated to the backend service.

## Risks / Trade-offs

- [Risk] Drag-and-drop requires client-only rendering in Next.js App Router. → Mitigation: wrap the board in a "use client" component and configure `@dnd-kit` sensors for pointer and keyboard.
- [Risk] Hidden columns and overdue highlighting require careful CSS; may need kanban-specific styles added to `globals.css`. → Mitigation: keep styles minimal and reuse existing color variables.
- [Risk] Task detail modal content can become large (sub-tasks + comments). → Mitigation: lazy-load comments only when modal opens; cap initial comment list.
- [Risk] Internal API routes duplicate backend URL paths. → Mitigation: keep route handlers thin one-line proxies.

## Migration Plan

1. Add internal API route handlers for tasks and kanban.
2. Build reusable components (`KanbanBoard`, `KanbanColumn`, `KanbanTaskCard`, `CreateTaskModal`, `TaskDetail`, `KanbanConfigForm`).
3. Add `/kanban` and `/kanban/config` pages.
4. Update `Sidebar.tsx` with new navigation entries.
5. Add kanban-specific styles to `globals.css`.
6. Smoke test against running backend.

## Open Questions

- Should task detail be a modal always, or a dedicated `/tasks/[task_id]` page? (Decision: modal for MVP.)
  - kanban上支持快捷编辑，但是task需要一个单独的页面
- Should the sidebar "创建 Task" button open a general task create modal, or also allow creating from a specific brief? (Decision: general modal; context-specific creation can be added later.)
  - sidebar 的“创建 Task” 打开一个general task create modal

