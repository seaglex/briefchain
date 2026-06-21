## ADDED Requirements

### Requirement: Create feedback
The system SHALL allow participants to create feedback on a brief.

#### Scenario: Successful progress feedback
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/feedbacks` with type `progress` and content
- **THEN** the system creates a feedback record and returns the feedback details

#### Scenario: Feedback creation rejected for invalid type
- **WHEN** an authenticated user sends a POST request to `/api/v1/briefs/:brief_id/feedbacks` with an invalid type
- **THEN** the system returns a 422 error

#### Scenario: Feedback creation rejected for non-participant
- **WHEN** a user who is neither `created_by` nor `assigned_to` sends a POST request to `/api/v1/briefs/:brief_id/feedbacks`
- **THEN** the system returns a 403 error

### Requirement: List feedbacks
The system SHALL return a list of feedbacks for a brief.

#### Scenario: Successful feedback list
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/feedbacks`
- **THEN** the system returns feedbacks with id, type, from_user, and created_at

#### Scenario: Filter feedbacks by type
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/feedbacks?type=progress`
- **THEN** the system returns only feedbacks with type `progress`

### Requirement: Get feedback detail
The system SHALL return the full content of a single feedback.

#### Scenario: Successful feedback detail
- **WHEN** an authenticated user sends a GET request to `/api/v1/feedbacks/:feedback_id`
- **THEN** the system returns the feedback with full content and attachments

#### Scenario: Feedback not found
- **WHEN** an authenticated user sends a GET request to `/api/v1/feedbacks/:feedback_id` for a non-existent feedback
- **THEN** the system returns a 404 error
