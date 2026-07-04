## Context

BriefChain separates cross-team brief contracts from team-internal execution. The brief layer is already implemented; this change adds the Task & Kanban execution layer on the backend.

The design is driven by:

- `docs/mvp_design/06-task-kanban-design.md` — data model and conceptual rules
- `docs/mvp_design/07-task-kanban-api-design.md` — endpoint contracts and behavior

Existing backend stack: FastAPI + SQLAlchemy 2.0 + Alembic, Pydantic schemas in `briefchain/api/schemas/`, business logic in `briefchain/api/services/`, and route modules in `briefchain/api/routes/`. The new code follows the same layout.

## Goals / Non-Goals

**Goals:**

- Provide Task CRUD, drag-to-change-status, and soft-delete with cascading sub-task/comment deletion.
- Provide Task Comment CRUD.
- Provide personal Kanban board query that renders columns dynamically from a user's default kanban + template.
- Provide Kanban configuration endpoints with automatic fork logic for shared templates.
- Provide read-only public-template listing/preview for the config page.
- Keep `tasks` and `kanbans` fully decoupled: a task stores only `status`, never a kanban or column reference.

**Non-Goals:**

- Team kanban query (`GET /kanban/team/:team_id`) — out of MVP scope.
- `customized` kanban mode or `task_columns` ordering table — reserved for future.
- Swimlane UI rendering — backend computes swimlanes but frontend MVP uses `group=none`.
- Public template creation/editing endpoints beyond listing and preview.
- Automatic brief completion when tasks are done.

## Decisions

### 1. Dedicated Kanban service owns the kanban ↔ template relationship

A single `briefchain/api/services/kanban.py` module will encapsulate all logic that touches both `kanbans` and `kanban_templates`/`kanban_template_columns`.

- Routes such as `GET /kanban/personal`, `PUT /kanbans/:id/columns`, and `POST /kanbans` call this service; they do not read or write `kanban_templates` directly.
- The service decides when to fork a template (user does not own the current template) and updates the `kanbans.kanban_template_id` reference transparently.
- This keeps the public API surface small: clients interact with kanban resources, while template internals remain an implementation detail.

**Rationale:** The product requirement says kanban templates are usually not exposed directly; rendering and editing flow through the kanban API. A dedicated service is the cleanest place to enforce that boundary.

### 2. Task status is the only bridge between tasks and a kanban board

`tasks.status` uses a global enum (`backlog`, `todo`, `in_progress`, `in_review`, `done`). The kanban board query fetches the user's default `kanbans` record, loads its template columns, and maps tasks into columns by matching `status` to `kanban_template_columns.status_key`.

- No `kanban_id` or `column_id` is stored on `tasks`.
- Dragging a task to another column updates `tasks.status` (and optionally `assignee_id`), not a column mapping.

**Rationale:** Full decoupling keeps task operations simple and lets the same task appear in different boards/views without data duplication. It matches the domain model in the design docs.

### 3. Use the existing cursor-pagination helper pattern for task/template lists

Task list, comment list, and public-template list use the same base64-encoded JSON cursor pattern already used for briefs. The board endpoint does not paginate because an MVP board is expected to fit in memory; future work can add column-level caged pagination if needed.

**Rationale:** Consistency with the existing codebase and the API design doc.

### 4. Permission model (MVP simplification)

- `created_by` has full control over a task.
- `assignee_id` can drag/change status and update assignable fields.
- For comments, only `created_by` can edit or delete.

**Rationale:** Matches the design doc and avoids introducing a separate role/ACL table for MVP.

### 5. Auto-initialize default kanbans out of this change's immediate scope

The migration seeds the global default template. 
A `POST /kanbans` endpoint is provided as a fallback so the frontend can create a board if one is missing.
The frontend will create a board with default template.

**Rationale:** Keeps the backend API change focused.

### 6. Soft-delete for tasks and cascade to sub-tasks/comments

Deleting a task sets `is_deleted=true`, `deleted_at=NOW()`, `deleted_by=JWT.user_id`, and applies the same soft-delete to all `parent_task_id = task_id` rows and all related `task_comments`.

**Rationale:** Replaces a `cancelled` status, preserves history, and matches existing brief patterns.

## Risks / Trade-offs

- [Risk] Queries that render the whole board load all visible tasks in one request; large boards could become slow. → Mitigation: MVP limits usage to personal boards; add per-column pagination/caching later if measured.
- [Risk] Forking templates on every column edit may create many private templates. → Mitigation: Acceptable for MVP; future work can add garbage collection or explicit "save as template" flow.
- [Risk] Name snapshots on tasks/comments become stale if a user renames themselves. → Mitigation: By design; snapshots reflect the name at the time of operation, matching briefs.
- [Risk] `status` values are global strings, so customized-mode columns will need a migration later. → Mitigation: The `kanban_template_mode` column is already part of the model to distinguish simple vs. customized when that mode arrives.

## Migration Plan

1. Add Alembic migration creating `tasks`, `kanban_templates`, `kanbans`, `kanban_template_columns`, and `task_comments`.
2. Seed `kanban_templates` id=1, `kanban_template_mode=simple`, plus five default `kanban_template_columns` rows.
3. Update `alembic/env.py` to import the new model modules so `autogenerate`/`target_metadata` sees them.
4. Update `src/briefchain/models/__init__.py` and `models/enums.py` with new exports.
5. Implement service modules and routes, then register them in `api/main.py`.
6. Run backend tests / manual smoke tests against the new endpoints.
7. Deploy migration; existing brief data is unaffected.

## Open Questions

- The frontend rely on `POST /kanbans` to create board when necessary
- Are team entities already implemented, or should team kanban initialization be deferred entirely? (Team board query is already out of MVP scope.)
  - No. Team entities are not implemented.
