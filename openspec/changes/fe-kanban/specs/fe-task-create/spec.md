## ADDED Requirements

### Requirement: Create-task modal supports task types
The system SHALL provide a modal that can create `task`, `bug`, or `sub_task`. The modal SHALL enforce type-specific validation: `sub_task` requires `parent_task_id`.

#### Scenario: Create a task
- **WHEN** the user opens the create modal, selects type "task", enters a title, and submits
- **THEN** the system calls `POST /api/v1/tasks` and closes the modal

#### Scenario: Reject sub_task without parent
- **WHEN** the user selects type "sub_task" without providing a parent task
- **THEN** the system shows a validation error and does not submit

### Requirement: Create-task modal can be opened from sidebar and column headers
The system SHALL open the same create-task modal from the sidebar "创建 Task" button and from each kanban column header's "新建" button.

#### Scenario: Create from sidebar
- **WHEN** the user clicks "创建 Task" in the sidebar
- **THEN** the modal opens with no pre-filled status

#### Scenario: Create from column header
- **WHEN** the user clicks "新建" in the "todo" column
- **THEN** the modal opens with status pre-filled to "todo"

### Requirement: Create-task modal captures optional fields
The system SHALL allow the user to set brief, title, content, priority, assignee, estimated hours, and due date before creating.

#### Scenario: Create with full fields
- **WHEN** the user fills all optional fields and submits
- **THEN** the system sends the complete payload to `POST /api/v1/tasks`
