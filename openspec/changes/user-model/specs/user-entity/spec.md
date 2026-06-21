## ADDED Requirements

### Requirement: User entity supports multiple user types
The system SHALL provide a `User` SQLAlchemy model that stores the user identifier, email, phone, name, avatar URL, user type, password hash, source system, external reference, and timestamps.

#### Scenario: Create a registered user
- **WHEN** a user registers with email and password
- **THEN** a `User` row is inserted with `user_type` set to "registered" and `password_hash` populated

#### Scenario: Create an external user
- **WHEN** an external BriefChain instance references a local user
- **THEN** a `User` row is inserted with `user_type` set to "external", `source_system` populated, and `external_ref` equal to the external user identifier

#### Scenario: Create a temporary user
- **WHEN** an upstream sends a brief to an external email address
- **THEN** a `User` row is inserted with `user_type` set to "temporary" and `email` populated

### Requirement: User type uses a defined enumeration
The system SHALL restrict `User.user_type` to the values "registered", "oauth", "external", and "temporary".

#### Scenario: Invalid user type is rejected
- **WHEN** code attempts to assign an unsupported value to `User.user_type`
- **THEN** the assignment is rejected by the `UserType` enumeration

### Requirement: User relationships are navigable
The system SHALL define a SQLAlchemy relationship from `User` to its identities.

#### Scenario: Load user with identities
- **WHEN** a user with OAuth bindings is queried
- **THEN** the `identities` relationship returns the associated `UserIdentity` instances
