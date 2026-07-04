## ADDED Requirements

### Requirement: Config page loads current kanban settings
The system SHALL provide a `/kanban/config` page that loads the user's kanban configuration (`/api/v1/kanbans/:id`) and available templates.

#### Scenario: Load config
- **WHEN** the user navigates to `/kanban/config`
- **THEN** the system displays the current template, group setting, done-visible-days, and column list

### Requirement: User can switch kanban template
The system SHALL allow the user to select a different template from the public/own template list and apply it.

#### Scenario: Switch template
- **WHEN** the user selects a template and saves
- **THEN** the system calls `PUT /api/v1/kanbans/:id` with `kanban_template_id` and refreshes the column list

### Requirement: User can edit group and done-visible-days
The system SHALL provide controls for `group` and `done_visible_days` and persist them on save.

#### Scenario: Change done-visible-days
- **WHEN** the user changes "done 显示天数" to 7 and saves
- **THEN** the system calls `PUT /api/v1/kanbans/:id` with the new value

### Requirement: User can edit column names and colors
The system SHALL allow editing each visible column's `name` and `color`. The system SHALL preserve `status_key` and `position` because the backend is in simple mode.

#### Scenario: Rename a column
- **WHEN** the user renames the "todo" column to "待办" and saves
- **THEN** the system sends the full column list to `PUT /api/v1/kanbans/:id/columns` and updates the displayed columns

### Requirement: Config page supports saving as public template
The system SHALL show a "保存为公开模板" option when the current template is owned by the user and is not already public. When checked, the system SHALL include a `name` for the public template in the save payload.

#### Scenario: Save private changes without publishing
- **WHEN** the user saves column edits without checking "保存为公开模板"
- **THEN** the system sends `is_public=false` (or omits it) and the backend forks/updates privately

#### Scenario: Publish template
- **WHEN** the user checks "保存为公开模板", enters a template name, and saves
- **THEN** the system sends `is_public=true` and the provided template name
