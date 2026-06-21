## ADDED Requirements

### Requirement: List brief versions
The system SHALL return a list of all versions for a brief.

#### Scenario: Successful version list
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/versions`
- **THEN** the system returns all versions with version number, title, modified_by, modified_at, change_summary, is_upstream_changed, and revision_reason

#### Scenario: Version list for non-existent brief
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/versions` for a non-existent brief
- **THEN** the system returns a 404 error

### Requirement: Get specific version detail
The system SHALL return the full content of a specific brief version through a dedicated endpoint.

#### Scenario: Get historical version content
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/versions/:version`
- **THEN** the system returns the brief content for the requested version with `is_current` set to `true` only when it matches `current_version`

#### Scenario: Requested version not found
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/versions/:version` for a version that does not exist
- **THEN** the system returns a 404 error
