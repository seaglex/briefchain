## ADDED Requirements

### Requirement: Sidebar exposes kanban navigation group
The system SHALL add a new navigation group in the sidebar containing "创建 Task" and "个人 kanban" entries.

#### Scenario: View sidebar
- **WHEN** the user is logged in and views the sidebar
- **THEN** the sidebar shows the new group with both entries

### Requirement: Sidebar entries navigate correctly
The system SHALL make "创建 Task" open the create-task modal and "个人 kanban" navigate to `/kanban`.

#### Scenario: Click 个人 kanban
- **WHEN** the user clicks "个人 kanban"
- **THEN** the browser navigates to `/kanban`

#### Scenario: Click 创建 Task
- **WHEN** the user clicks "创建 Task"
- **THEN** the create-task modal opens without changing the current page

### Requirement: Active sidebar state highlights the kanban entry
The system SHALL visually highlight the "个人 kanban" entry when the user is on `/kanban` or `/kanban/config`.

#### Scenario: Active kanban route
- **WHEN** the user is on `/kanban/config`
- **THEN** the "个人 kanban" sidebar entry is marked active
