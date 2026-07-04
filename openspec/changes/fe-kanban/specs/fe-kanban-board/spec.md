## ADDED Requirements

### Requirement: Personal kanban page loads the user's board
The system SHALL provide a `/kanban` page that fetches the authenticated user's personal kanban board from the backend and renders it.

#### Scenario: Board exists
- **WHEN** the user navigates to `/kanban`
- **THEN** the system fetches `/api/v1/kanban/personal` and displays the kanban columns and task cards

#### Scenario: Board does not exist
- **WHEN** the user navigates to `/kanban` and the backend returns `KANBAN_NOT_FOUND`
- **THEN** the system calls `POST /api/v1/kanbans` to create a default board and reloads the page

### Requirement: Board renders columns according to template configuration
The system SHALL render one column per visible `kanban_template_columns` entry, ordered by `position`, using the column's `name`, `color`, and task count in the column header.

#### Scenario: Render visible columns
- **WHEN** the board response contains todo, in_progress, in_review, and done columns
- **THEN** the page displays four columns in that order, each with the configured header color and a "新建" button

#### Scenario: Hidden columns are collapsed
- **WHEN** a column has `is_hidden=true`
- **THEN** the system renders it as a folded column at roughly 20% width, showing only the task count

### Requirement: Task cards display key information
The system SHALL render each task card with title, priority badge, assignee name, and due date. Cards whose due date is in the past SHALL be highlighted in red.

#### Scenario: Normal task card
- **WHEN** a column contains a task with title, priority, assignee, and future due date
- **THEN** the card shows all fields without red highlighting

#### Scenario: Overdue task card
- **WHEN** a task's due date is before now
- **THEN** the card is visually marked as overdue

### Requirement: Task cards can be dragged to another column
The system SHALL allow the user to drag a task card from one column to another using `@dnd-kit/core` + `@dnd-kit/sortable`. On drop in a different column, the system SHALL call `PUT /api/tasks/:task_id/drag` with the target column's `status_key` and refresh the board on success.

#### Scenario: Drag task to in_progress
- **WHEN** the user drags a card from "todo" and drops it in "in_progress"
- **THEN** the system sends `{ "status": "in_progress" }` to the drag endpoint and re-fetches the board

#### Scenario: Drag task to its current column
- **WHEN** the user drags a card but drops it in the same column
- **THEN** the system does not call the drag endpoint and the card remains in place

### Requirement: Board provides navigation to detail and config
The system SHALL provide a way to open a task's detail view and a button to navigate to the kanban config page.

#### Scenario: Open task detail
- **WHEN** the user clicks "查看详情" on a task card
- **THEN** the system opens the Task detail modal

#### Scenario: Open config page
- **WHEN** the user clicks the configuration button in the top-right corner
- **THEN** the system navigates to `/kanban/config`
