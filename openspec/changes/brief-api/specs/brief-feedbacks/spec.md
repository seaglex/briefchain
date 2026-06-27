## ADDED Requirements

### Requirement: List feedbacks
The system SHALL return a paginated list of feedbacks for a brief.

#### Scenario: Successful feedback list
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/feedbacks`
- **THEN** the system returns feedbacks with `id`, `brief_id`, `brief_version`, `is_to_down`, `type`, `from_user_id`, `from_user_name`, `to_user_id`, `to_user_name`, and `created_at`

#### Scenario: Filter feedbacks by type
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/feedbacks?type=progress`
- **THEN** the system returns only feedbacks with `type` equal to "progress"

#### Scenario: Filter feedbacks by direction
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/feedbacks?is_to_down=false`
- **THEN** the system returns only feedbacks where `is_to_down` is false

#### Scenario: Feedback list for non-existent brief
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/feedbacks` for a non-existent brief
- **THEN** the system returns a 404 error

### Requirement: Get feedback detail
The system SHALL return the full content of a single feedback.

#### Scenario: Successful feedback detail
- **WHEN** an authenticated user sends a GET request to `/api/v1/feedbacks/:feedback_id`
- **THEN** the system returns the feedback with `id`, `brief_id`, `brief_version`, `is_to_down`, `type`, `content`, `attachments`, `from_user_id`, `from_user_name`, `to_user_id`, `to_user_name`, `is_auto_generated`, `confirmed_at`, `created_at`, and `updated_at`

#### Scenario: Feedback not found
- **WHEN** an authenticated user sends a GET request to `/api/v1/feedbacks/:feedback_id` for a non-existent feedback
- **THEN** the system returns a 404 error

### Requirement: Feedbacks are created by lifecycle endpoints
The system SHALL create feedback records via the `/briefs/:brief_id/upstream-actions` and `/briefs/:brief_id/downstream-actions` endpoints; the direct feedback endpoints only support listing and detail retrieval.

#### Scenario: Progress feedback via downstream action
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/downstream-actions?action=process` with content
- **THEN** the system creates a feedback record with `type` "progress" and `is_to_down` false, which is then visible in the feedback list
