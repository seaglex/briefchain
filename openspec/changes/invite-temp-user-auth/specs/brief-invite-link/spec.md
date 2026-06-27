## ADDED Requirements

### Requirement: Generate invite link for external recipient
The system SHALL create an invite link when `POST /briefs/:brief_id/transfer?action=send` receives `is_temporary_user=true` and an optional `recipient_email` or `recipient_phone`.

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
- **WHEN** a `POST /invites/{token}/transfer?action=accept` request uses a valid token and the brief `upstream_state` is `sent`
- **THEN** the system sets `upstream_state` to `in_process` and `downstream_state` to `opened`, records `accepted_at` in the transfer history, and returns the updated brief and transfer

#### Scenario: Accept with invalidated token fails
- **WHEN** a recipient tries to accept using a token already marked invalidated
- **THEN** the system returns `410 Gone` with code `INVITE_INVALIDATED`

### Requirement: Reject brief via invite token
The system SHALL allow a recipient to reject a sent brief using only the invite token and provide a rejection reason.

#### Scenario: Reject with valid token
- **WHEN** a `POST /invites/{token}/transfer?action=reject` request uses a valid token, the brief `upstream_state` is `sent`, and a reason is provided
- **THEN** the system sets `upstream_state` to `editing`, clears `downstream_state` (sets to `null`), records `rejected_at` and `rejection_reason` in the transfer history, and returns the updated brief and transfer

#### Scenario: Reject without reason fails
- **WHEN** a reject request omits the `reason` field
- **THEN** the system returns `422 Unprocessable Entity`

### Requirement: Downstream actions via invite token
The system SHALL allow a recipient to perform downstream actions on an `in_process` brief using only the invite token. All actions map to `POST /invites/{token}/downstream-actions?action=<action>` and use the same request/response shape as the authenticated downstream-actions endpoint.

#### Scenario: Submit completion with valid token
- **WHEN** a `POST /invites/{token}/downstream-actions?action=submit` request uses a valid token, the brief `upstream_state` is `in_process`, and `content` completion notes are provided
- **THEN** the system sets `downstream_state` to `submitted`, creates a feedback record with `type` "submit" and `is_to_down` false, and returns the updated brief and feedback

#### Scenario: Submit without content fails
- **WHEN** a submit request omits the `content` field
- **THEN** the system returns `422 Unprocessable Entity`

#### Scenario: Block with valid token
- **WHEN** a `POST /invites/{token}/downstream-actions?action=block` request uses a valid token, the brief `upstream_state` is `in_process`, and a `content` blocker reason is provided
- **THEN** the system sets `downstream_state` to `blocked`, creates a feedback record with `type` "block" and `is_to_down` false, and returns the updated brief and feedback

#### Scenario: Block without content fails
- **WHEN** a block request omits the `content` field
- **THEN** the system returns `422 Unprocessable Entity`

#### Scenario: Open with valid token
- **WHEN** a `POST /invites/{token}/downstream-actions?action=open` request uses a valid token, the brief `upstream_state` is `in_process`, and a `content` reopen reason is provided
- **THEN** the system sets `downstream_state` to `opened`, creates a feedback record with `type` "open" and `is_to_down` false, and returns the updated brief and feedback

#### Scenario: Delegate with valid token
- **WHEN** a `POST /invites/{token}/downstream-actions?action=delegate` request uses a valid token and the brief `upstream_state` is `in_process`
- **THEN** the system sets `downstream_state` to `delegated`, creates a feedback record with `type` "delegate" and `is_to_down` false, and returns the updated brief and feedback

#### Scenario: Progress feedback with valid token
- **WHEN** a `POST /invites/{token}/downstream-actions?action=process` request uses a valid token and the brief `upstream_state` is `in_process`
- **THEN** the system leaves `upstream_state` and `downstream_state` unchanged and creates a feedback record with `type` "progress" and `is_to_down` false
