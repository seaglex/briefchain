## ADDED Requirements

### Requirement: User can list accessible kanban templates
The system SHALL provide `GET /kanban-templates` returning public templates and any private templates created by the authenticated user, paginated with a cursor.

#### Scenario: List includes public and own private templates
- **WHEN** an authenticated user sends `GET /kanban-templates`
- **THEN** the system returns templates where `is_public=true` or `created_by` equals the JWT user_id

#### Scenario: Exclude other users' private templates
- **WHEN** an authenticated user sends `GET /kanban-templates`
- **THEN** the system does not return private templates owned by other users

### Requirement: User can preview a template and its columns
The system SHALL provide `GET /kanban-templates/:kanban_template_id` returning the template summary and its column configuration, provided the template is public or owned by the requesting user.

#### Scenario: Preview public template
- **WHEN** an authenticated user sends `GET /kanban-templates/1`
- **THEN** the system returns HTTP 200 with the template and its columns

#### Scenario: Cannot preview private foreign template
- **WHEN** an authenticated user sends `GET /kanban-templates/:id` for a private template created by another user
- **THEN** the system returns HTTP 403 with code `FORBIDDEN`
