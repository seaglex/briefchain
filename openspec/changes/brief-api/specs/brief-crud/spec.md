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
- **THEN** the system returns the brief with its current sent version content, `version` equals `current_version`, `is_current` is `true`, and `draft_version` is the version number of any editable draft if one exists, otherwise `null`

#### Scenario: Get detail with editable draft
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id` and `current_version` is 1 while version 2 exists as `draft`
- **THEN** the system returns the brief with version 1 content, `version` equals 1, `is_current` is `true`, and `draft_version` is 2

#### Scenario: Get historical version
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id?version=1`
- **THEN** the system returns the brief content for version 1, `is_current` is `true` only when version 1 equals `current_version`, and `draft_version` is the version number of any editable draft if one exists, otherwise `null`

#### Scenario: Brief not found
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id` for a non-existent brief
- **THEN** the system returns a 404 error

### Requirement: Patch brief content
The system SHALL allow the creator to patch a brief version whenever the brief is not in a terminal `upstream_state` (`done` or `cancelled`).

#### Scenario: Successful patch before any version is sent
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=patch` with updated title, content, priority, or expected_completion_at
- **THEN** the system updates the existing draft version in place, does NOT synchronize `briefs.title` / `priority` / `expected_completion_at` (only `send` or `update` updates those denormalized fields), and returns the updated brief with the patched version number and `draft_version` set to that version number

#### Scenario: Successful patch after a version was sent and rejected
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=patch` and the current version status is `sent` (e.g., after the brief was rejected back to `editing`)
- **THEN** the system creates a new draft version with the next version number, leaves `current_version` pointing to the old sent version, leaves `briefs.title` / `priority` unchanged, and returns the updated brief with `draft_version` set to the new draft version number

#### Scenario: Patch on sent version rejected when draft already exists
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=patch` and a higher draft version already exists
- **THEN** the system returns a 409 error with code `DRAFT_ALREADY_EXISTS`

#### Scenario: Patch rejected for terminal upstream state
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=patch` when `upstream_state` is `done` or `cancelled`
- **THEN** the system returns a 409 error

#### Scenario: Patch rejected for non-creator
- **WHEN** a user who is not the creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=patch`
- **THEN** the system returns a 403 error

### Requirement: Submit brief version for review
The system SHALL allow the creator to submit the current draft version for review via `action=submit-review`, transitioning the version status to "reviewed" and leaving `briefs.upstream_state` unchanged.

#### Scenario: Successful review submission
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=submit-review` with an optional note
- **THEN** the system updates the current draft `BriefVersion.status` to "reviewed", records the effective `arbiter_review_id` on the version, leaves `briefs.upstream_state` unchanged (patch/submit-review only operate on version, not brief state), and returns the brief with the reviewed version

#### Scenario: Review submission rejected for non-creator
- **WHEN** a non-creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=submit-review`
- **THEN** the system returns a 403 error

#### Scenario: Review submission rejected when current version is not draft
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/editing?action=submit-review` when the current version status is not "draft"
- **THEN** the system returns a 409 error
