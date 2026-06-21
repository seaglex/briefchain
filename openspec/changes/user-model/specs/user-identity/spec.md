## ADDED Requirements

### Requirement: User identity stores OAuth binding
The system SHALL provide a `UserIdentity` SQLAlchemy model that stores the identity identifier, user identifier, provider, provider user identifier, and timestamp.

#### Scenario: Bind a GitHub identity
- **WHEN** a registered user binds a GitHub account
- **THEN** a `UserIdentity` row is inserted with `provider` set to "github" and `provider_user_id` set to the GitHub user identifier

### Requirement: Provider and provider user id are unique together
The system SHALL enforce a unique constraint on `(provider, provider_user_id)` to prevent duplicate bindings.

#### Scenario: Duplicate provider binding is rejected
- **WHEN** code attempts to insert a `UserIdentity` row with the same `provider` and `provider_user_id` as an existing row
- **THEN** the database raises a unique constraint violation

### Requirement: User identity is linked to its user
The system SHALL define a SQLAlchemy relationship from `UserIdentity` to `User` and from `User` to its identities.

#### Scenario: List user identities
- **WHEN** the identities of a user are requested
- **THEN** the `identities` relationship returns all associated `UserIdentity` rows
