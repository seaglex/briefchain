## ADDED Requirements

### Requirement: User can retrieve kanban configuration
The system SHALL provide `GET /kanbans/:kanban_id` returning the kanban record, its referenced template summary, and the full column configuration, provided the requesting user owns the kanban.

#### Scenario: Get personal kanban config
- **WHEN** an authenticated user sends `GET /kanbans/:kanban_id` for their own board
- **THEN** the system returns HTTP 200 with `kanban`, `template`, and `columns`

#### Scenario: Cannot access another user's kanban
- **WHEN** an authenticated user sends `GET /kanbans/:kanban_id` for a board owned by another user
- **THEN** the system returns HTTP 403 with code `FORBIDDEN`

### Requirement: User can update kanban settings
The system SHALL allow the kanban owner to update `name`, `kanban_template_id`, `group`, and `done_visible_days`. Changing the template SHALL also update the redundant `kanban_template_mode` field.

#### Scenario: Switch template
- **WHEN** the owner sends `PUT /kanbans/:kanban_id` with `kanban_template_id=2`
- **THEN** the system updates the kanban and returns the new configuration with columns from the selected template

### Requirement: User can create a personal kanban
The system SHALL provide `POST /kanbans` to create a kanban for the authenticated user, defaulting to the global template and `group=none`. The owner_id SHALL be the JWT user_id.

#### Scenario: Create fallback board
- **WHEN** an authenticated user sends `POST /kanbans` with `owner_type=user`
- **THEN** the system creates the board and returns HTTP 201

### Requirement: Column updates flow through the kanban endpoint and fork shared templates
The system SHALL provide `PUT /kanbans/:kanban_id/columns` to accept a full column configuration. If the current template is owned by another user (or is a public system template), the system SHALL create a private copy of the template, update the kanban to reference the copy, and apply the column changes to the copy. If the current template is owned by the requesting user, the system SHALL update the existing template directly.

#### Scenario: Fork public template on column rename
- **WHEN** the owner sends `PUT /kanbans/:kanban_id/columns` with a renamed column and the current template is not owned by the user
- **THEN** the system creates a private `kanban_template`, updates the kanban's `kanban_template_id` to it, and returns the updated kanban and new columns

#### Scenario: Update own template directly
- **WHEN** the owner sends `PUT /kanbans/:kanban_id/columns` and the current template's `created_by` equals the JWT user_id
- **THEN** the system updates the existing template's columns and returns the updated configuration

#### Scenario: Preserve status_key and position in simple mode
- **WHEN** the owner sends column updates for a simple-mode template
- **THEN** the system rejects any attempt to change `status_key` or `position` and returns HTTP 422
