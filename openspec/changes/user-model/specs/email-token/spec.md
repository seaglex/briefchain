## ADDED Requirements

### Requirement: Email token stores temporary user access grant
The system SHALL provide an `EmailToken` SQLAlchemy model that stores the token, email, brief identifier, expiration time, and usage time.

#### Scenario: Create email token
- **WHEN** an upstream sends a brief to an external email address
- **THEN** an `EmailToken` row is inserted with `token` set to a random GUID, `email` populated, `brief_id` populated, and `expires_at` set in the future

### Requirement: Email token tracks usage
The system SHALL record when an email token is used to prevent replay attacks.

#### Scenario: Use email token
- **WHEN** a temporary user clicks the email link
- **THEN** the corresponding `EmailToken` row has `used_at` set to the current time

### Requirement: Email token is associated with a brief
The system SHALL store the brief identifier in `EmailToken.brief_id`.

#### Scenario: Verify token validity
- **WHEN** a token is verified
- **THEN** the system returns the associated brief identifier and title
