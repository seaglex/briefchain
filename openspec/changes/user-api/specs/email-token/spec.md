## ADDED Requirements

### Requirement: Verify email token
The system SHALL validate an email token and return the associated brief information.

> **Implementation Note**: Email-token access for temporary users is **not implemented in this change**. It is reserved for a follow-up change that will fully define the temporary-user lifecycle, email delivery flow, and brief hand-off state machine. The `EmailToken` model already exists in the database layer and remains untouched.

#### Scenario: Valid token
- **WHEN** a client sends a GET request to `/api/v1/tokens/:token/verify` with an unused, non-expired token
- **THEN** the system returns valid=true, brief_id, brief_title, and action

#### Scenario: Invalid or expired token
- **WHEN** a client sends a GET request to `/api/v1/tokens/:token/verify` with an expired, used, or non-existent token
- **THEN** the system returns valid=false and appropriate error details

### Requirement: Accept brief via email token
The system SHALL allow a temporary user to accept a brief using an email token.

> **Implementation Note**: This endpoint is **not implemented in this change**.

#### Scenario: Successful acceptance
- **WHEN** a client sends a POST request to `/api/v1/tokens/:token/accept` with a valid token
- **THEN** the system marks the brief as accepted, records the acceptance, and returns the updated brief

#### Scenario: Acceptance with invalid token
- **WHEN** a client sends a POST request to `/api/v1/tokens/:token/accept` with an invalid token
- **THEN** the system returns a 401 or 404 error

### Requirement: Reject brief via email token
The system SHALL allow a temporary user to reject a brief using an email token.

> **Implementation Note**: This endpoint is **not implemented in this change**.

#### Scenario: Successful rejection
- **WHEN** a client sends a POST request to `/api/v1/tokens/:token/reject` with a valid token and a reason
- **THEN** the system marks the brief as draft, records the rejection reason, and returns the updated brief

#### Scenario: Rejection with missing reason
- **WHEN** a client sends a POST request to `/api/v1/tokens/:token/reject` without a reason
- **THEN** the system returns a 422 error

#### Scenario: Rejection with invalid token
- **WHEN** a client sends a POST request to `/api/v1/tokens/:token/reject` with an invalid token
- **THEN** the system returns a 401 or 404 error
