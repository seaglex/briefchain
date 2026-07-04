## ADDED Requirements

### Requirement: User can retrieve their personal kanban board
The system SHALL provide `GET /kanban/personal` that returns the authenticated user's default personal kanban configuration and a set of columns populated from the active template and matching tasks.

#### Scenario: Default board exists
- **WHEN** an authenticated user sends `GET /kanban/personal`
- **THEN** the system returns the kanban config, visible columns, and grouped tasks in swimlanes

#### Scenario: Fallback when default board missing
- **WHEN** an authenticated user sends `GET /kanban/personal` but no default board exists
- **THEN** the system returns HTTP 404 with code `KANBAN_NOT_FOUND` and a message indicating the board is missing

### Requirement: Board columns are rendered from the kanban template
The system SHALL load `kanban_template_columns` for the user's current `kanban_template_id`, exclude columns marked `is_hidden=true`, order them by `position`, and group tasks by matching `status_key`.

#### Scenario: Render simple-mode columns
- **WHEN** the user's default kanban uses a simple template with columns todo, in_progress, in_review, done
- **THEN** the response contains those columns and each visible task appears in the column matching its `status`

### Requirement: Done column respects done_visible_days
The system SHALL include `done` tasks only when `updated_at` is within `kanbans.done_visible_days` of the current time.

#### Scenario: Hide old done tasks
- **WHEN** a done task was last updated 20 days ago and the kanban's `done_visible_days` is 14
- **THEN** the system excludes that task from the done column

### Requirement: Board supports swimlane grouping
The system SHALL group tasks within each column into swimlanes according to the kanban's `group` setting: `none`, `assignee`, `brief`, or `priority`. The `group` value MAY be overridden by a query parameter.

#### Scenario: Group by assignee
- **WHEN** the user's kanban has `group=assignee` and a column contains tasks assigned to two different users
- **THEN** the response contains one swimlane per assignee_name, each containing the matching tasks

#### Scenario: No grouping
- **WHEN** the user's kanban has `group=none`
- **THEN** the response contains a single swimlane with `swimlane_key=null` per column
