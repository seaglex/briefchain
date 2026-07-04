## Why

BriefChain currently supports cross-team brief contracts, but has no execution layer for teams or individuals to track day-to-day work. We need a lightweight Task & Kanban backend so users can create tasks, drag them through a workflow, and view a personal board without coupling tasks to any particular board layout.

## What Changes

- Add SQLAlchemy models and Alembic migration for `tasks`, `kanbans`, `kanban_templates`, `kanban_template_columns`, and `task_comments`.
- Seed a global default kanban template (`kanban_template_id=1`) with the standard `simple` columns: backlog, todo, in_progress, in_review, done.
- Implement Task CRUD API (`POST /tasks`, `GET /tasks`, `GET /tasks/:id`, `PUT /tasks/:id`, `DELETE /tasks/:id`) plus a drag endpoint (`PUT /tasks/:id/drag`) for status changes.
- Implement Task Comment API (`GET/POST /tasks/:id/comments`, `PUT/DELETE /comments/:id`).
- Implement Kanban query API (`GET /kanban/personal`) that returns columns + swimlanes computed dynamically from the user's default kanban configuration and matching tasks.
- Implement Kanban configuration API (`GET /kanbans/:id`, `PUT /kanbans/:id`, `POST /kanbans`, `PUT /kanbans/:id/columns`) with automatic fork logic when a user modifies a shared template they do not own.
- Implement Kanban template listing/preview API (`GET /kanban-templates`, `GET /kanban-templates/:id`) for selecting templates in the config page.
- Add a dedicated kanban service that owns the relationship between `kanbans` and `kanban_templates` so routes do not expose template internals directly.

## Capabilities

### New Capabilities

- `task-crud`: Create, list, retrieve, update, drag, and soft-delete tasks. Includes permission checks (creator full control, assignee can drag/change status) and name snapshots.
- `task-comments`: Create, list, update, and delete plain comments on tasks.
- `kanban-board`: Query the authenticated user's personal kanban board. Computes columns from the user's default kanban + template and groups tasks into swimlanes based on `group` setting.
- `kanban-config`: Manage kanban-level settings (name, template, group, done-visible-days) and column configuration, with backend fork logic for shared templates.
- `kanban-template`: List and preview public (or own) kanban templates for selection in the config page.

### Modified Capabilities

- None. This change only adds new backend capabilities; it does not alter existing Brief/Feedback behavior, although future work may auto-create tasks from briefs.

## Impact

- New database tables and an Alembic migration.
- New FastAPI routers: `tasks`, `kanban`, `kanbans`, `kanban-templates`, plus new service modules and Pydantic schemas.
- Updates to `models/enums.py` for task/kanban enums and to `main.py` to register routers.
- User registration / team creation flows will eventually auto-initialize a default personal/team kanban (hooked later).
