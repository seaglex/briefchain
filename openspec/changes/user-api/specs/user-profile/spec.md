## ADDED Requirements

### Requirement: List users
The system SHALL return a paginated list of users with sensitive information masked for non-self and non-admin viewers.

#### Scenario: Successful user list
- **WHEN** a client sends a GET request to `/api/v1/users` with a valid token
- **THEN** the system returns a list of users with id, name, avatar_url, and masked email/phone

### Requirement: Get single user
The system SHALL return a single user's profile with sensitive information masked based on the viewer's identity.

#### Scenario: View own profile
- **WHEN** a client sends a GET request to `/api/v1/users/:user_id` for their own user_id
- **THEN** the system returns the full profile including unmasked email and phone

#### Scenario: View another user's profile
- **WHEN** a client sends a GET request to `/api/v1/users/:user_id` for a different user
- **THEN** the system returns the profile with masked email and phone

#### Scenario: User not found
- **WHEN** a client sends a GET request to `/api/v1/users/:user_id` for a non-existent user
- **THEN** the system returns a 404 error
