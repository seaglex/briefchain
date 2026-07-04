## ADDED Requirements

### Requirement: Authenticated user can create a task
The system SHALL allow an authenticated user to create a task. The creator's `user_id` and name SHALL be captured from the JWT token and stored as `created_by` and `created_by_name`. The task type SHALL be one of `task`, `bug`, or `sub_task`. A `sub_task` SHALL require `parent_task_id`. A `task` or `bug` SHALL accept an optional `brief_id`. The initial status SHALL default to `todo` when not provided.

#### Scenario: Create a top-level task
- **WHEN** an authenticated user sends `POST /tasks` with `type=task`, `title`, and optional fields
- **THEN** the system creates the task, returns HTTP 201, and the response includes the task with `created_by` equal to the JWT user_id

#### Scenario: Reject sub_task without parent_task_id
- **WHEN** an authenticated user sends `POST /tasks` with `type=sub_task` and no `parent_task_id`
- **THEN** the system returns HTTP 422 with code `VALIDATION_ERROR`

### Requirement: User can list tasks with filters
The system SHALL return a paginated list of tasks visible to the authenticated user, supporting filters by `brief_id`, `type`, `status`, `team_id`, `assignee_id`, and `priority`. The list SHALL exclude `content` and SHALL use cursor-based pagination.

#### Scenario: List personal tasks
- **WHEN** an authenticated user sends `GET /tasks?status=todo`
- **THEN** the system returns only non-deleted tasks matching the filter with `next_cursor`

### Requirement: User can retrieve task details
The system SHALL return the full task detail, including `content`, the five most recent comments, and any sub-tasks, when the user requests `GET /tasks/:task_id`.

#### Scenario: Get existing task
- **WHEN** an authenticated user sends `GET /tasks/:task_id` for an existing task
- **THEN** the system returns HTTP 200 with the task, `sub_tasks`, and `comments`

### Requirement: Creator or assignee can update a task
The system SHALL allow the task creator or the current assignee to update editable fields. Updating `status` SHALL record `status_changed_by` and `status_changed_at`. Updating `assignee_id` SHALL refresh `assignee_name` from the users table.

#### Scenario: Creator updates priority
- **WHEN** the task creator sends `PUT /tasks/:task_id` with `priority=p0`
- **THEN** the system returns HTTP 200 with the updated task

#### Scenario: Assignee changes status
- **WHEN** the assignee sends `PUT /tasks/:task_id` with `status=in_progress`
- **THEN** the system records `status_changed_by` as the assignee and returns the updated task

### Requirement: Creator or assignee can drag a task to change status
The system SHALL provide `PUT /tasks/:task_id/drag` to move a task to a target column by updating `status`. The endpoint MAY also update `assignee_id` when the drag crosses swimlanes.

#### Scenario: Drag task to in_progress
- **WHEN** the creator sends `PUT /tasks/:task_id/drag` with `status=in_progress`
- **THEN** the system updates the task status, records the changer, and returns the updated task

### Requirement: Only the creator can soft-delete a task
The system SHALL allow only the task creator to delete a task. Deletion SHALL be a soft delete and SHALL cascade to all sub-tasks and related comments.

#### Scenario: Creator deletes task with sub-tasks and comments
- **WHEN** the creator sends `DELETE /tasks/:task_id`
- **THEN** the system marks the task, its sub-tasks, and its comments as deleted and returns HTTP 204

#### Scenario: Non-creator cannot delete
- **WHEN** a user who is not the creator sends `DELETE /tasks/:task_id`
- **THEN** the system returns HTTP 403 with code `FORBIDDEN`
