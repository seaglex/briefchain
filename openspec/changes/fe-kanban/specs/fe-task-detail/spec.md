## ADDED Requirements

### Requirement: Task detail view shows task information
The system SHALL display the task's title, content, status, priority, assignee, estimated/actual hours, due date, creator, and timestamps.

#### Scenario: Open task detail
- **WHEN** the user opens a task detail modal
- **THEN** the system fetches `/api/v1/tasks/:task_id` and displays all fields

### Requirement: Editable fields can be updated by authorized users
The system SHALL allow the creator or assignee to update title, content, status, priority, assignee, estimated hours, actual hours, and due date. The creator SHALL also be able to delete the task.

#### Scenario: Creator updates priority
- **WHEN** the creator changes the priority and saves
- **THEN** the system calls `PUT /api/v1/tasks/:task_id` and refreshes the view

#### Scenario: Creator deletes task
- **WHEN** the creator clicks delete and confirms
- **THEN** the system calls `DELETE /api/v1/tasks/:task_id`, closes the modal, and refreshes the board

### Requirement: Task detail lists sub-tasks
The system SHALL display the task's sub-tasks (from `sub_tasks` in the detail response) as a compact list.

#### Scenario: View sub-tasks
- **WHEN** the task has sub-tasks
- **THEN** the system renders each sub-task title with a link to open its detail

### Requirement: Task detail supports comments
The system SHALL list the latest comments and allow the user to add, edit, and delete their own comments.

#### Scenario: Add comment
- **WHEN** the user enters a comment and submits
- **THEN** the system calls `POST /api/v1/tasks/:task_id/comments` and appends the comment

#### Scenario: Edit own comment
- **WHEN** the user edits their own comment
- **THEN** the system calls `PUT /api/v1/comments/:comment_id` and updates the comment

#### Scenario: Delete own comment
- **WHEN** the user deletes their own comment
- **THEN** the system calls `DELETE /api/v1/comments/:comment_id` and removes the comment
