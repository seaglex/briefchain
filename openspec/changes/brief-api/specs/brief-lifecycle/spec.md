## ADDED Requirements

### Requirement: Submit brief for review
The system SHALL allow the creator to submit a draft brief for review, transitioning its status to `reviewed`.

#### Scenario: Successful submission
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/submit`
- **THEN** the system updates the brief status to `reviewed` and returns the updated brief

#### Scenario: Submission rejected for non-creator
- **WHEN** a non-creator sends a POST request to `/api/v1/briefs/:brief_id/submit`
- **THEN** the system returns a 403 error

#### Scenario: Submission rejected for non-draft status
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/submit` when status is not `draft`
- **THEN** the system returns a 409 error

### Requirement: Send brief to downstream
The system SHALL allow the creator to send a reviewed brief to a downstream user, transitioning its status to `sent`.

#### Scenario: Successful send
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/send` with `assigned_to`
- **THEN** the system updates the brief status to `sent`, sets `assigned_to`, creates a transfer record, and returns the brief and transfer

#### Scenario: Send rejected for non-reviewed status
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/send` when status is not `reviewed`
- **THEN** the system returns a 409 error

### Requirement: Accept brief
The system SHALL allow the assigned downstream user to accept a sent brief, transitioning its status to `accepted`.

#### Scenario: Successful acceptance
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/accept`
- **THEN** the system updates the brief status to `accepted`, records `accepted_at` on the transfer, and returns the updated brief

#### Scenario: Acceptance rejected for non-assigned user
- **WHEN** a user other than `assigned_to` sends a POST request to `/api/v1/briefs/:brief_id/accept`
- **THEN** the system returns a 403 error

### Requirement: Reject brief
The system SHALL allow the assigned downstream user to reject a sent brief, transitioning its status back to `draft`.

#### Scenario: Successful rejection with reason
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/reject` with a reason
- **THEN** the system updates the brief status to `draft`, records `rejected_at` and `rejection_reason` on the transfer, and returns the updated brief

#### Scenario: Rejection rejected without reason
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/reject` without a reason
- **THEN** the system returns a 422 error

### Requirement: Cancel brief
The system SHALL allow the creator to cancel a brief that is not already `done`.

#### Scenario: Successful cancellation
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/cancel`
- **THEN** the system updates the brief status to `cancelled` and returns the updated brief

#### Scenario: Cancel rejected for done brief
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/cancel` when status is `done`
- **THEN** the system returns a 409 error

### Requirement: Complete brief
The system SHALL allow the assigned downstream user to mark an accepted brief as `done`.

#### Scenario: Successful completion
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/complete`
- **THEN** the system updates the brief status to `done` and returns the updated brief

#### Scenario: Completion rejected for non-accepted status
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/complete` when status is not `accepted`
- **THEN** the system returns a 409 error
