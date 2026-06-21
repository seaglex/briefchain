## ADDED Requirements

### Requirement: User registration
The system SHALL allow a new user to register with email or phone and a password.

#### Scenario: Successful registration with email
- **WHEN** a client sends a POST request to `/api/v1/auth/register` with a valid email, password, and name
- **THEN** the system creates a registered user and returns the user object with a JWT token

#### Scenario: Successful registration with phone
- **WHEN** a client sends a POST request to `/api/v1/auth/register` with a valid phone, password, and name
- **THEN** the system creates a registered user and returns the user object with a JWT token

#### Scenario: Registration rejects missing email and phone
- **WHEN** a client sends a POST request to `/api/v1/auth/register` without email and phone
- **THEN** the system returns a 422 error indicating that at least one contact method is required

#### Scenario: Registration rejects duplicate email
- **WHEN** a client sends a POST request to `/api/v1/auth/register` with an email already in use
- **THEN** the system returns a 409 error indicating the email is already registered

#### Scenario: Registration rejects duplicate phone
- **WHEN** a client sends a POST request to `/api/v1/auth/register` with a phone already in use
- **THEN** the system returns a 409 error indicating the phone is already registered

### Requirement: User login
The system SHALL authenticate a registered user with email/phone and password and return a JWT token.

#### Scenario: Successful login with email
- **WHEN** a client sends a POST request to `/api/v1/auth/login` with a registered email and correct password
- **THEN** the system returns the user object with a JWT token

#### Scenario: Successful login with phone
- **WHEN** a client sends a POST request to `/api/v1/auth/login` with a registered phone and correct password
- **THEN** the system returns the user object with a JWT token

#### Scenario: Login rejects invalid credentials
- **WHEN** a client sends a POST request to `/api/v1/auth/login` with an unknown email or wrong password
- **THEN** the system returns a 401 error indicating invalid credentials

### Requirement: Get current user
The system SHALL return the currently authenticated user's profile.

#### Scenario: Successful current user retrieval
- **WHEN** a client sends a GET request to `/api/v1/auth/me` with a valid Bearer token
- **THEN** the system returns the current user's profile

#### Scenario: Current user rejects unauthenticated requests
- **WHEN** a client sends a GET request to `/api/v1/auth/me` without a valid token
- **THEN** the system returns a 401 error

### Requirement: User logout
The system SHALL expose a logout endpoint for clients to clear authentication state.

#### Scenario: Successful logout
- **WHEN** a client sends a POST request to `/api/v1/auth/logout` with a valid Bearer token
- **THEN** the system returns a 204 No Content response

#### Scenario: OAuth login is not supported in MVP
- **WHEN** a client requests WeChat or other OAuth login
- **THEN** the system SHALL NOT implement OAuth login in this change
