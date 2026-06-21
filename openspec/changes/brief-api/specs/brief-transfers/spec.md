## ADDED Requirements

### Requirement: List transfer history
The system SHALL return the transfer history for a brief.

#### Scenario: Successful transfer list
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/transfers`
- **THEN** the system returns all transfer records including from_user, to_user, brief_version, sent_at, accepted_at, rejected_at, and rejection_reason

#### Scenario: Transfer list for non-existent brief
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/transfers` for a non-existent brief
- **THEN** the system returns a 404 error

### Requirement: Transfer record reflects lifecycle actions
The system SHALL create or update transfer records when a brief is sent, accepted, or rejected.

#### Scenario: Send creates transfer record
- **WHEN** the creator sends a brief to a downstream user
- **THEN** the system creates a transfer record with `sent_at` populated and `accepted_at`/`rejected_at` null

#### Scenario: Accept updates transfer record
- **WHEN** the assigned user accepts a sent brief
- **THEN** the system updates the latest pending transfer record with `accepted_at`

#### Scenario: Reject updates transfer record
- **WHEN** the assigned user rejects a sent brief with a reason
- **THEN** the system updates the latest pending transfer record with `rejected_at` and `rejection_reason`
