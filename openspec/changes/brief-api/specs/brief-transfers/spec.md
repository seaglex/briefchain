## ADDED Requirements

### Requirement: Send brief to downstream
The system SHALL allow the creator to send a reviewed or previously-sent brief to a downstream user. `send` is the invitation-phase bridge: it transitions the current version to `sent`, synchronizes `briefs.current_version` / `title` / `priority` / `expected_completion_at`, and transitions `upstream_state` to "sent" (or keeps it "sent" when replacing an existing invitation).

#### Scenario: Successful send to registered user
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/transfer?action=send` with `is_temporary_user` false and `assigned_to` set to a registered user
- **THEN** the system verifies the current version status is "reviewed" or "sent", sets `briefs.upstream_state` to "sent", sets `assigned_to` and `assigned_to_name`, updates `briefs.current_version`, `title`, `priority`, and `expected_completion_at` to the sent version, creates a `BriefTransferHistory` record with `from_user_name` and `to_user_name` snapshots, and returns the brief and transfer

#### Scenario: Successful send to temporary user
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/transfer?action=send` with `is_temporary_user` true and optional recipient contact info
- **THEN** the system creates or resolves a temporary user, sets `assigned_to` and `assigned_to_name`, sets `upstream_state` to "sent", creates a transfer record with name snapshots, creates a `BriefInvite`, and returns the brief, transfer, and invite details

#### Scenario: Send rejected for non-sendable version
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/transfer?action=send` when the current version status is not "reviewed" or "sent"
- **THEN** the system returns a 409 error

#### Scenario: Replacement send keeps upstream_state as sent
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/transfer?action=send` while `upstream_state` is already "sent" or when `upstream_state` is "editing" after a previous rejection (with the current version still "sent")
- **THEN** the system keeps `upstream_state` as "sent", transitions the current version to "sent" if it was "reviewed", updates `assigned_to` and `assigned_to_name` to the new recipient, creates a new `BriefTransferHistory` record, and returns the brief and transfer

#### Scenario: Send rejected for non-creator
- **WHEN** a non-creator sends a POST request to `/api/v1/briefs/:brief_id/transfer?action=send`
- **THEN** the system returns a 403 error

### Requirement: Accept brief
The system SHALL allow the assigned downstream user to accept a sent brief.

#### Scenario: Successful acceptance
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/transfer?action=accept` with an optional note
- **THEN** the system sets `briefs.upstream_state` to "in_process" and `downstream_state` to "opened", does NOT modify `current_version` or any `BriefVersion.status`, updates `status_changed_at` / `status_changed_by`, updates the latest pending transfer record with `accepted_at`, and returns the updated brief and transfer

#### Scenario: Acceptance rejected for non-assigned user
- **WHEN** a user other than `assigned_to` sends a POST request to `/api/v1/briefs/:brief_id/transfer?action=accept`
- **THEN** the system returns a 403 error

#### Scenario: Acceptance rejected for non-sent brief
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/transfer?action=accept` when `upstream_state` is not "sent"
- **THEN** the system returns a 409 error

### Requirement: Reject brief
The system SHALL allow the assigned downstream user to reject a sent brief.

#### Scenario: Successful rejection with reason
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/transfer?action=reject` with a required `reason`
- **THEN** the system sets `briefs.upstream_state` to "editing", clears `assigned_to` and `assigned_to_name`, does NOT modify `current_version` or any `BriefVersion.status`, updates `status_changed_at` / `status_changed_by`, updates the latest pending transfer record with `rejected_at` and `rejection_reason`, and returns the updated brief and transfer

#### Scenario: Rejection rejected without reason
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/transfer?action=reject` without a reason
- **THEN** the system returns a 422 error

#### Scenario: Rejection rejected for non-sent brief
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/transfer?action=reject` when `upstream_state` is not "sent"
- **THEN** the system returns a 409 error

### Requirement: List transfer history
The system SHALL return the transfer history for a brief.

#### Scenario: Successful transfer list
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/transfers`
- **THEN** the system returns all transfer records including `from_user_id`, `from_user_name`, `to_user_id`, `to_user_name`, `brief_version`, `sent_at`, `accepted_at`, `rejected_at`, and `rejection_reason`

#### Scenario: Transfer list for non-existent brief
- **WHEN** an authenticated user sends a GET request to `/api/v1/briefs/:brief_id/transfers` for a non-existent brief
- **THEN** the system returns a 404 error
