## ADDED Requirements

### Requirement: List brief versions
The system SHALL return a list of all versions for a brief.

#### Scenario: Successful version list
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/versions`
- **THEN** the system returns all versions with `version`, `status`, `title`, `modified_by_id`, `modified_by_name`, `modified_at`, `change_summary`, `is_upstream_changed`, and `revision_reason`
- **AND** the returned list includes versions whose `status` is `draft`, `reviewed`, or `sent`

#### Scenario: Version list for non-existent brief
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/versions` for a non-existent brief
- **THEN** the system returns a 404 error

### Requirement: Get specific version content
The system SHALL return the full content of a specific brief version through the brief detail endpoint.

#### Scenario: Get historical version content
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id?version=1`
- **THEN** the system returns the brief content for version 1 with `is_current` set to `true` only when version 1 matches `current_version`

#### Scenario: Get current version by default
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id` without a `version` parameter
- **THEN** the system returns the current sent version content, `is_current` is `true`, and `draft_version` indicates the editable draft version number if one exists, otherwise `null`

#### Scenario: Requested version not found
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id?version=999` for a version that does not exist
- **THEN** the system returns a 404 error
