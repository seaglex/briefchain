## ADDED Requirements

### Requirement: Register with brief ID upgrades temporary user in place
The system SHALL allow a `POST /auth/register` request to include an optional `brief_id`; when valid, the temporary user currently assigned to that brief is upgraded to `registered` and retains the same UUID.

#### Scenario: Successful upgrade from temporary user
- **WHEN** a registration request provides `email`, `password`, `name`, and a valid `brief_id` whose `assigned_to` is a temporary user
- **THEN** the system updates the existing temporary user row to `user_type="registered"`, sets `password_hash`, updates `email`/`name`, sets `users.from_temporary_user_id` to the temporary user's own UUID, marks the invite's `final_user_id` to the registered user's UUID, invalidates the brief's invite, and returns a JWT for the same UUID

#### Scenario: Upgrade migrates all active briefs to registered user
- **WHEN** a temporary user successfully registers with `brief_id`
- **THEN** the system updates `assigned_to` to the registered user's UUID for all briefs assigned to the temporary user whose status is not `done` and not `cancelled`

#### Scenario: Invalid brief ID is rejected
- **WHEN** a registration request provides a `brief_id` that does not exist or is not assigned to a temporary user
- **THEN** the system returns `400 Bad Request` with code `INVALID_BRIEF_ID`

#### Scenario: Email already registered during upgrade
- **WHEN** a registration request with `brief_id` uses an email already registered to another user
- **THEN** the system returns `409 Conflict` with code `EMAIL_ALREADY_REGISTERED`

### Requirement: Login with brief ID links brief ownership
The system SHALL allow a `POST /auth/login` request to include an optional `brief_id`; when valid, the briefs currently assigned to a temporary user are reassigned to the logged-in registered user.

#### Scenario: Login links sent brief from temporary user
- **WHEN** a login request provides valid credentials for a registered user and a valid `brief_id` whose `assigned_to` is a temporary user in `sent` status
- **THEN** the system updates all active briefs' `assigned_to` to the registered user's UUID, sets `users.from_temporary_user_id` on the registered user to the temporary user's UUID, marks the invite's `final_user_id` to the registered user's UUID, invalidates the corresponding invite, and returns the registered user's JWT

#### Scenario: Login migrates all active briefs to registered user
- **WHEN** a registered user logs in with a `brief_id` and the temporary user has multiple briefs in `sent` and `accepted` status
- **THEN** the system updates `assigned_to` to the registered user's UUID for all briefs assigned to the temporary user whose status is not `done` and not `cancelled`

#### Scenario: Historical transfer records remain unchanged after login link
- **WHEN** a temporary user's brief ownership is migrated to a registered user via login
- **THEN** existing transfer history rows keep `to_user` pointing to the temporary user UUID

#### Scenario: Invalid brief ID on login is rejected
- **WHEN** a login request provides a `brief_id` that does not exist or is not assigned to a temporary user
- **THEN** the system returns `400 Bad Request` with code `INVALID_BRIEF_ID`

### Requirement: Upgrade or login records final user and invalidates invite
The system SHALL mark the invite linked to a temporary user with `final_user_id` and `invalidated_at` when that temporary user is upgraded or linked through login.

#### Scenario: Register records final user and invalidates invite
- **WHEN** a temporary user successfully registers
- **THEN** the corresponding `BriefInvite` row has `final_user_id` set to the registered user's UUID and `invalidated_at` set to the current timestamp

#### Scenario: Login records final user and invalidates invite
- **WHEN** a registered user logs in with a `brief_id`
- **THEN** the corresponding `BriefInvite` row has `final_user_id` set to the registered user's UUID and `invalidated_at` set to the current timestamp
