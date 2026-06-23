## ADDED Requirements

### Requirement: Create temporary user during external send
The system SHALL create a `temporary` user row when a brief is sent to an external email or phone that does not match any registered user.

#### Scenario: Temporary user is created with optional contact info
- **WHEN** a brief is sent to `recipient_email="lisi@example.com"` and `recipient_name="李四"`
- **THEN** the system creates a user with `user_type="temporary"`, `name="李四"`, `email="lisi@example.com"`, and `password_hash=null`

#### Scenario: Temporary user cannot authenticate with password
- **WHEN** a login request uses credentials matching a `temporary` user's email or phone
- **THEN** the system returns `401 Unauthorized` with code `TEMPORARY_USER_CANNOT_LOGIN`

### Requirement: Temporary user has no password-based login capability
The system SHALL reject any password login attempt for users where `user_type` is `temporary`.

#### Scenario: Login with temporary user email fails
- **WHEN** a `POST /auth/login` request uses an email that belongs to a temporary user
- **THEN** the system returns `401 Unauthorized` regardless of whether the password matches

### Requirement: Temporary user can operate on briefs via invite token
The system SHALL allow a temporary user to view, accept, reject, block, and complete assigned briefs through the invite token endpoint without requiring JWT authentication.

#### Scenario: Invite endpoint returns brief assigned to temporary user
- **WHEN** a valid invite token is presented
- **THEN** the returned brief has `assigned_to` equal to the temporary user's UUID
