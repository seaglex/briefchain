## ADDED Requirements

### Requirement: Create brief
The system SHALL allow an authenticated user to create a new brief.

#### Scenario: Successful creation of a root brief
- **WHEN** an authenticated user sends a POST request to `/api/v1/briefs` with title, content, priority, and estimated_man_days
- **THEN** the system creates a root brief with status `draft`, current_version `1`, and returns the brief details

#### Scenario: Successful creation of a child brief
- **WHEN** an authenticated user sends a POST request to `/api/v1/briefs` with a valid `parent_id`
- **THEN** the system creates a child brief, sets `root_id` to the parent's root_id, and returns the brief details

#### Scenario: Creation rejects missing title
- **WHEN** an authenticated user sends a POST request to `/api/v1/briefs` without a title
- **THEN** the system returns a 422 error

### Requirement: List briefs
The system SHALL return a paginated list of briefs filtered by role and status.

#### Scenario: List briefs created by current user
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs?role=created`
- **THEN** the system returns briefs where `created_by` equals the current user

#### Scenario: List briefs assigned to current user
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs?role=assigned`
- **THEN** the system returns briefs where `assigned_to` equals the current user

#### Scenario: List briefs by status
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs?status=draft`
- **THEN** the system returns only briefs with status `draft`

### Requirement: Get brief detail
The system SHALL return the detail of a single brief, always showing its latest version content.

#### Scenario: Get current version
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id`
- **THEN** the system returns the brief with its current (latest) version content, `version` equals `current_version`, and `is_current` is `true`

#### Scenario: Brief not found
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id` for a non-existent brief
- **THEN** the system returns a 404 error

### Requirement: Update brief
The system SHALL allow the creator to update a brief only when it is in `draft` status.

#### Scenario: Successful update
- **WHEN** the creator sends a PATCH request to `/api/v1/briefs/:brief_id` with updated title, content, or priority
- **THEN** the system increments `current_version`, creates a new brief_version record, and returns the updated brief

#### Scenario: Update rejected for non-draft status
- **WHEN** the creator sends a PATCH request to `/api/v1/briefs/:brief_id` with status other than `draft`
- **THEN** the system returns a 409 error

#### Scenario: Update rejected for non-creator
- **WHEN** a user who is not the creator sends a PATCH request to `/api/v1/briefs/:brief_id`
- **THEN** the system returns a 403 error
