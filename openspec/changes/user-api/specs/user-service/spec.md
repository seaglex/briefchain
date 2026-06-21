## ADDED Requirements

### Requirement: User registration service
The system SHALL provide a service function to register a new user with email or phone and a password.

#### Scenario: Successful registration
- **WHEN** `register_user(session, request)` is called with a valid email or phone, name, and password
- **THEN** it creates a registered user, hashes the password, and returns the user with a JWT token

#### Scenario: Registration rejects missing contact
- **WHEN** `register_user(session, request)` is called without email and phone
- **THEN** it raises a validation error indicating at least one contact method is required

#### Scenario: Registration rejects duplicate email
- **WHEN** `register_user(session, request)` is called with an email already in use
- **THEN** it raises a conflict error indicating the email is already registered

#### Scenario: Registration rejects duplicate phone
- **WHEN** `register_user(session, request)` is called with a phone already in use
- **THEN** it raises a conflict error indicating the phone is already registered

### Requirement: User login service
The system SHALL provide a service function to authenticate a registered user and return a JWT token.

#### Scenario: Successful login
- **WHEN** `login_user(session, request)` is called with a registered email or phone and correct password
- **THEN** it returns the user with a JWT token

#### Scenario: Login rejects invalid credentials
- **WHEN** `login_user(session, request)` is called with an unknown email/phone or wrong password
- **THEN** it raises an authentication error

### Requirement: Get current user profile service
The system SHALL provide a service function to return the currently authenticated user's profile.

#### Scenario: Successful current user retrieval
- **WHEN** `get_current_user_profile(current_user)` is called
- **THEN** it returns the user profile with unmasked email and phone

### Requirement: List users service
The system SHALL provide a service function to return a paginated list of users with sensitive information masked for non-self viewers.

#### Scenario: Successful user list
- **WHEN** `list_users(session, viewer_user_id, page, page_size)` is called
- **THEN** it returns a paginated list of users with id, name, avatar_url, and masked email/phone

### Requirement: Get single user service
The system SHALL provide a service function to return a single user's profile with sensitive information masked based on the viewer's identity.

#### Scenario: View own profile
- **WHEN** `get_user_by_id(session, user_id, viewer_user_id)` is called with the user's own id
- **THEN** it returns the full profile including unmasked email and phone

#### Scenario: View another user's profile
- **WHEN** `get_user_by_id(session, user_id, viewer_user_id)` is called with a different user id
- **THEN** it returns the profile with masked email and phone

#### Scenario: User not found
- **WHEN** `get_user_by_id(session, user_id, viewer_user_id)` is called for a non-existent user
- **THEN** it raises a not-found error

### Requirement: Email-token service is out of scope
The system SHALL NOT implement email-token service functions in this change.

#### Scenario: Accept and reject via email token are deferred
- **WHEN** a service for accepting or rejecting a brief via email token is requested
- **THEN** the implementation is deferred to the follow-up change that defines the temporary-user lifecycle and brief hand-off state machine
