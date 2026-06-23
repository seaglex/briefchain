## ADDED Requirements

### Requirement: Generate invite link for external recipient
The system SHALL create an invite link when `POST /briefs/:brief_id/send` receives `is_temporary_user=true` and an optional `recipient_email` or `recipient_phone`.

#### Scenario: Send with is_temporary_user and no contact creates anonymous temporary user
- **WHEN** an authenticated user sends a reviewed brief with `is_temporary_user=true` and no `recipient_email` or `recipient_phone`
- **THEN** the system creates a new `temporary` user without contact info, assigns the brief to that user, creates a `BriefInvite` record, and returns an `invite_url`

#### Scenario: Send to external email creates temporary user and invite
- **WHEN** an authenticated user sends a reviewed brief with `is_temporary_user=true` and `recipient_email="lisi@example.com"`
- **THEN** the system creates a `temporary` user, assigns the brief to that user, creates a `BriefInvite` record with a unique nonce and HMAC token, creates a transfer history record, and returns an `invite_url`

#### Scenario: Existing registered email falls back to registered send
- **WHEN** an authenticated user sends a brief with `is_temporary_user=true` and `recipient_email` that matches an existing registered user
- **THEN** the system uses the registered user UUID as `assigned_to`, does not create a temporary user, and returns the normal send response without an invite URL

#### Scenario: Existing temporary email with final_user_id falls back to registered send
- **WHEN** an authenticated user sends a brief with `is_temporary_user=true` and `recipient_email` that matches a temporary user who has `final_user_id` set
- **THEN** the system uses the `final_user_id` as `assigned_to`, does not create a new user, and returns the normal send response without an invite URL

#### Scenario: Existing temporary email without final_user_id reuses user_id
- **WHEN** an authenticated user sends a brief with `is_temporary_user=true` and `recipient_email` that matches a temporary user with no `final_user_id`
- **THEN** the system reuses the existing temporary user UUID, assigns the brief to that user, creates a new `BriefInvite` record, and returns an `invite_url`

### Requirement: Validate invite token
The system SHALL validate the HMAC signature, expiration, and database nonce before allowing any `/invites/{token}` operation.

#### Scenario: Valid token returns invite details
- **WHEN** a request provides a token with a correct HMAC signature, unexpired deadline, and existing nonce
- **THEN** the system returns the invitee name, sender info, deadlines, full brief details, and the brief_id

#### Scenario: Tampered token is rejected without DB lookup
- **WHEN** a request provides a token whose HMAC signature does not match the reconstructed payload
- **THEN** the system returns `401 Unauthorized` with code `INVITE_INVALID_TOKEN`

#### Scenario: Expired token is rejected
- **WHEN** a request provides a token whose `accept_deadline_epoch` is in the past
- **THEN** the system returns `410 Gone` with code `INVITE_EXPIRED`

#### Scenario: Invalidated token is rejected
- **WHEN** a request provides a token whose `BriefInvite.invalidated_at` is not null
- **THEN** the system returns `410 Gone` with code `INVITE_INVALIDATED`

### Requirement: Accept brief via invite token
The system SHALL allow a recipient to accept a sent brief using only the invite token, without JWT authentication.

#### Scenario: Accept with valid token
- **WHEN** a `POST /invites/{token}/accept` request uses a valid token and the brief status is `sent`
- **THEN** the system changes the brief status to `accepted`, records `accepted_at` in the transfer history, and returns the updated brief and transfer

#### Scenario: Accept with invalidated token fails
- **WHEN** a recipient tries to accept using a token already marked invalidated
- **THEN** the system returns `410 Gone` with code `INVITE_INVALIDATED`

### Requirement: Reject brief via invite token
The system SHALL allow a recipient to reject a sent brief using only the invite token and provide a rejection reason.

#### Scenario: Reject with valid token
- **WHEN** a `POST /invites/{token}/reject` request uses a valid token, the brief status is `sent`, and a reason is provided
- **THEN** the system changes the brief status to `draft`, records `rejected_at` and `rejection_reason` in the transfer history, and returns the updated brief and transfer

#### Scenario: Reject without reason fails
- **WHEN** a reject request omits the `reason` field
- **THEN** the system returns `422 Unprocessable Entity`

### Requirement: Mark brief blocked via invite token
The system SHALL allow a recipient to report a brief as blocked using only the invite token and provide a reason.

#### Scenario: Block with valid token
- **WHEN** a `POST /invites/{token}/blocked` request uses a valid token, the brief status is `accepted`, and a reason is provided
- **THEN** the system changes the brief status to `blocked`, creates a `blocked` feedback with the provided reason, and returns the updated brief and feedback

#### Scenario: Block without reason fails
- **WHEN** a block request omits the `reason` field
- **THEN** the system returns `422 Unprocessable Entity`

### Requirement: Mark brief done via invite token
The system SHALL allow a recipient to mark a brief as done using only the invite token and provide a completion result.

#### Scenario: Done with valid token
- **WHEN** a `POST /invites/{token}/done` request uses a valid token, the brief status is `accepted`, and a result is provided
- **THEN** the system changes the brief status to `done`, creates a `completion` feedback with the provided result, and returns the updated brief and feedback

#### Scenario: Done without result fails
- **WHEN** a done request omits the `result` field
- **THEN** the system returns `422 Unprocessable Entity`
