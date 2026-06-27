## ADDED Requirements

### Requirement: Create brief
The system SHALL allow an authenticated user to create a new brief.

#### Scenario: Successful creation of a root brief
- **WHEN** an authenticated user sends a POST request to `/api/v1/briefs` with title, content, attachments, priority, estimated_man_days, expected_completion_at, and parent_id omitted
- **THEN** the system creates a root brief with `upstream_state` set to "editing", `downstream_state` set to null, `current_version` set to null, copies `title` and `priority` to the brief row, stores the creator's name snapshot in `created_by_name`, and returns the brief details

#### Scenario: Successful creation of a child brief
- **WHEN** an authenticated user sends a POST request to `/api/v1/briefs` with a valid `parent_id`
- **THEN** the system creates a child brief, sets `root_id` to the parent's `root_id`, sets `is_root` to false, and returns the brief details

#### Scenario: Creation rejects missing title
- **WHEN** an authenticated user sends a POST request to `/api/v1/briefs` without a title
- **THEN** the system returns a 422 error

### Requirement: List briefs
The system SHALL return a paginated list of briefs filtered by role, upstream state, downstream state, and root chain.

#### Scenario: List briefs created by current user
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs?role=created`
- **THEN** the system returns briefs where `created_by` equals the current user

#### Scenario: List briefs assigned to current user
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs?role=assigned`
- **THEN** the system returns briefs where `assigned_to` equals the current user

#### Scenario: List briefs by upstream state
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs?upstream_state=editing`
- **THEN** the system returns only briefs with `upstream_state` equal to "editing"

#### Scenario: List briefs by downstream state
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs?downstream_state=opened`
- **THEN** the system returns only briefs with `downstream_state` equal to "opened"

### Requirement: Get brief detail
The system SHALL return the detail of a single brief, showing the requested version content.

#### Scenario: Get current version
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id`
- **THEN** the system returns the brief with its current sent version content, `version` equals `current_version`, and `is_current` is `true`

#### Scenario: Get historical version
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id?version=1`
- **THEN** the system returns the brief content for version 1 and `is_current` is `true` only when version 1 equals `current_version`

#### Scenario: Brief not found
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id` for a non-existent brief
- **THEN** the system returns a 404 error

### Requirement: Patch brief content
The system SHALL allow the creator to patch a brief only when `upstream_state` is "editing".

#### Scenario: Successful patch before any version is sent
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=patch` with updated title, content, priority, or expected_completion_at
- **THEN** the system updates the existing draft version in place, synchronizes `briefs.title` / `priority` / `expected_completion_at`, and returns the updated brief with the patched version number

#### Scenario: Successful patch after a version was sent and rejected
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=patch` and the current sent version was rejected back to editing
- **THEN** the system creates a new draft version with the next version number, leaves `current_version` pointing to the old sent version, leaves `briefs.title` / `priority` unchanged, and returns the updated brief with the new draft version number

#### Scenario: Patch rejected for non-editing upstream state
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=patch` when `upstream_state` is not "editing"
- **THEN** the system returns a 409 error

#### Scenario: Patch rejected for non-creator
- **WHEN** a user who is not the creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=patch`
- **THEN** the system returns a 403 error

### Requirement: Submit brief version for review
The system SHALL allow the creator to submit the current draft version for review, transitioning the version status to "reviewed".

#### Scenario: Successful review submission
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=review` with an optional note
- **THEN** the system updates the current draft `BriefVersion.status` to "reviewed", records the effective `arbiter_review_id` on the version, leaves `briefs.upstream_state` as "editing", and returns the brief with the reviewed version

#### Scenario: Review submission rejected for non-creator
- **WHEN** a non-creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=review`
- **THEN** the system returns a 403 error

#### Scenario: Review submission rejected when current version is not draft
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=review` when the current version status is not "draft"
- **THEN** the system returns a 409 error
