## ADDED Requirements

### Requirement: Register with invite token upgrades temporary user in place
The system SHALL allow a `POST /auth/register` request to include optional `temporary_user_id` and `invite_token`; when valid, the temporary user currently associated with the invite is upgraded to `registered` and retains the same UUID.

#### Scenario: Successful upgrade from temporary user
- **WHEN** a registration request provides `email`, `password`, `name`, and a valid `invite_token` whose associated temporary user matches the provided `temporary_user_id`
- **THEN** the system updates the existing temporary user row to `user_type="registered"`, sets `password_hash`, updates `email`/`name`, sets `users.from_temporary_user_id` to the temporary user's own UUID, marks the invite's `final_user_id` to the registered user's UUID, invalidates all invites linked to the temporary user, and returns a JWT for the same UUID

#### Scenario: Upgrade migrates all active briefs to registered user
- **WHEN** a temporary user successfully registers with `invite_token`
- **THEN** the system updates `assigned_to` to the registered user's UUID for all briefs assigned to the temporary user whose `upstream_state` is not `done` and not `cancelled`

#### Scenario: Invalid invite token or mismatched temporary user is rejected
- **WHEN** a registration request provides an `invite_token` that is invalid, expired, invalidated, or a `temporary_user_id` that does not match the invite's temporary user
- **THEN** the system returns `400 Bad Request` with code `INVALID_INVITE_TOKEN`

#### Scenario: Email already registered during upgrade
- **WHEN** a registration request with `invite_token` uses an email already registered to another user
- **THEN** the system returns `409 Conflict` with code `EMAIL_ALREADY_REGISTERED`

### Requirement: Login with invite token links brief ownership
The system SHALL allow a `POST /auth/login` request to include optional `temporary_user_id` and `invite_token`; when valid, the briefs currently assigned to the temporary user are reassigned to the logged-in registered user.

#### Scenario: Login links in_process brief from temporary user
- **WHEN** a login request provides valid credentials for a registered user and a valid `invite_token` whose associated temporary user matches the provided `temporary_user_id`
- **THEN** the system updates all active briefs' `assigned_to` to the registered user's UUID, sets `users.from_temporary_user_id` on the registered user to the temporary user's UUID, marks the invite's `final_user_id` to the registered user's UUID, invalidates all invites linked to the temporary user, and returns the registered user's JWT

#### Scenario: Login migrates all active briefs to registered user
- **WHEN** a registered user logs in with an `invite_token` and the temporary user has multiple active briefs
- **THEN** the system updates `assigned_to` to the registered user's UUID for all briefs assigned to the temporary user whose `upstream_state` is not `done` and not `cancelled`

#### Scenario: Historical transfer records remain unchanged after login link
- **WHEN** a temporary user's brief ownership is migrated to a registered user via login
- **THEN** existing transfer history rows keep `to_user` pointing to the temporary user UUID

#### Scenario: Invalid invite token or mismatched temporary user on login is rejected
- **WHEN** a login request provides an `invite_token` that is invalid, expired, invalidated, or a `temporary_user_id` that does not match the invite's temporary user
- **THEN** the system returns `400 Bad Request` with code `INVALID_INVITE_TOKEN`

### Requirement: Upgrade or login records final user and invalidates invite
The system SHALL mark the invite linked to a temporary user with `final_user_id` and `invalidated_at` when that temporary user is upgraded or linked through login.

#### Scenario: Register records final user and invalidates invite
- **WHEN** a temporary user successfully registers
- **THEN** the corresponding `BriefInvite` row has `final_user_id` set to the registered user's UUID and `invalidated_at` set to the current timestamp

#### Scenario: Login records final user and invalidates invite
- **WHEN** a registered user logs in with an `invite_token`
- **THEN** the corresponding `BriefInvite` row has `final_user_id` set to the registered user's UUID and `invalidated_at` set to the current timestamp
