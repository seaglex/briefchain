## 1. Data model and migration

- [x] 1.1 Add `TaskStatus`, `TaskType`, `TaskPriority`, `KanbanOwnerType`, and `KanbanGroup` enums to `src/briefchain/models/enums.py`
- [x] 1.2 Create `src/briefchain/models/kanban.py` with `Task`, `KanbanTemplate`, `KanbanTemplateColumn`, `Kanban`, and `TaskComment` SQLAlchemy models
- [x] 1.3 Export new models and enums from `src/briefchain/models/__init__.py`
- [x] 1.4 Import new models in `alembic/env.py` so `target_metadata` includes them
- [x] 1.5 Generate and review Alembic migration that creates the five new tables and seeds the global default template (`kanban_template_id=1`) with five columns

## 2. Task CRUD service

- [x] 2.1 Create `src/briefchain/api/services/tasks.py` with helpers for loading users/tasks, cursor pagination, and permission checks
- [x] 2.2 Implement `create_task` with validation for `type`, `parent_task_id`, and `brief_id`; snapshot creator/assignee names
- [x] 2.3 Implement `list_tasks` with filters and cursor pagination (exclude `content`)
- [x] 2.4 Implement `get_task_detail` returning task, sub-tasks, and latest 5 comments
- [x] 2.5 Implement `update_task` for partial updates, updating `status_changed_*` and `assignee_name` as needed
- [x] 2.6 Implement `drag_task` to update `status` (and optionally `assignee_id`) with status-changed metadata
- [x] 2.7 Implement `delete_task` soft-delete with cascade to sub-tasks and comments

## 3. Task Comment service

- [x] 3.1 Implement `list_task_comments` with cursor pagination in `src/briefchain/api/services/tasks.py`
- [x] 3.2 Implement `create_task_comment` snapshotting creator name
- [x] 3.3 Implement `update_task_comment` allowing only the creator
- [x] 3.4 Implement `delete_task_comment` allowing only the creator

## 4. Kanban service

- [x] 4.1 Create `src/briefchain/api/services/kanban.py` with a dedicated service that owns `kanbans` ↔ `kanban_templates` interactions
- [x] 4.2 Implement `get_personal_kanban_board` returning kanban config, columns, and swimlane-grouped tasks
- [x] 4.3 Implement `get_kanban_config` returning kanban + template summary + columns
- [x] 4.4 Implement `update_kanban_config` for `name`, `kanban_template_id`, `group`, and `done_visible_days`
- [x] 4.5 Implement `create_kanban` for personal fallback creation
- [x] 4.6 Implement `update_kanban_columns` with fork logic: clone template if not owned, then apply column changes

## 5. Schemas

- [x] 5.1 Create `src/briefchain/api/schemas/tasks.py` with request/response models for tasks, drag, list items, and detail
- [x] 5.2 Create `src/briefchain/api/schemas/kanban.py` with request/response models for kanban board, config, columns, and templates

## 6. Routes and wiring

- [x] 6.1 Create `src/briefchain/api/routes/tasks.py` with endpoints for task CRUD, drag, and comments
- [x] 6.2 Create `src/briefchain/api/routes/kanban.py` with endpoints for `/kanban/personal`, `/kanbans`, `/kanbans/:id`, `/kanbans/:id/columns`, and `/kanban-templates`
- [x] 6.3 Register new routers in `src/briefchain/api/main.py` under `/api/v1`
- [x] 6.4 Add router-level `get_current_user_id` dependency to all new protected routes

## 7. Validation and edge cases

- [x] 7.1 Validate `status_key` and `position` are immutable in simple mode column updates
- [x] 7.2 Ensure done-column tasks are filtered by `done_visible_days`
- [x] 7.3 Enforce `type=sub_task` requires `parent_task_id`; `sub_task` does not appear in kanban
- [x] 7.4 Return appropriate error codes (`TASK_NOT_FOUND`, `KANBAN_NOT_FOUND`, `FORBIDDEN`, `VALIDATION_ERROR`)

## 8. Verification

- [x] 8.1 Run `alembic upgrade head` successfully and inspect seeded default template
- [x] 8.2 Start the API and smoke-test task creation, board query, drag, and column-update fork flow
- [x] 8.3 Run the existing test suite to ensure no regressions
