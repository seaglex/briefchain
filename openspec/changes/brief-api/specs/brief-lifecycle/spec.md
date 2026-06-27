## ADDED Requirements

### Requirement: Cancel brief
The system SHALL allow the creator to cancel a brief that is not already terminal.

#### Scenario: Successful cancellation
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/upstream-actions?action=cancel` with a required `content` reason
- **THEN** the system sets `briefs.upstream_state` to "cancelled", preserves `downstream_state` for audit, updates `status_changed_at` / `status_changed_by`, creates a feedback record with `type` "cancel" and `is_to_down` true, and returns the updated brief

#### Scenario: Cancel rejected for done brief
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/upstream-actions?action=cancel` when `upstream_state` is "done"
- **THEN** the system returns a 409 error

#### Scenario: Cancel rejected for non-creator
- **WHEN** a non-creator sends a POST request to `/api/v1/briefs/:brief_id/upstream-actions?action=cancel`
- **THEN** the system returns a 403 error

### Requirement: Suspend and resume brief
The system SHALL allow the creator to suspend a brief from "sent" or "in_process" and later resume it.

#### Scenario: Successful suspension
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/upstream-actions?action=suspend` with a required `content` reason
- **THEN** the system sets `briefs.upstream_state` to "suspended", preserves `downstream_state`, updates `status_changed_at` / `status_changed_by`, creates a feedback record with `type` "suspend" and `is_to_down` true, and returns the updated brief

#### Scenario: Successful resume
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/upstream-actions?action=resume` with a required `content` reason
- **THEN** the system sets `briefs.upstream_state` back to "in_process", leaves `downstream_state` unchanged, updates `status_changed_at` / `status_changed_by`, creates a feedback record with `type` "resume" and `is_to_down` true, and returns the updated brief

#### Scenario: Suspend rejected for editing brief
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/upstream-actions?action=suspend` when `upstream_state` is "editing"
- **THEN** the system returns a 409 error

#### Scenario: Resume rejected for non-suspended brief
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/upstream-actions?action=resume` when `upstream_state` is not "suspended"
- **THEN** the system returns a 409 error

### Requirement: Approve submitted brief
The system SHALL allow the creator to approve a brief only when `downstream_state` is "submitted".

#### Scenario: Successful approval
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/upstream-actions?action=approve` with a required `content` acceptance note
- **THEN** the system sets `briefs.upstream_state` to "done" and `downstream_state` to null, updates `status_changed_at` / `status_changed_by`, creates a feedback record with `type` "approve" and `is_to_down` true, and returns the updated brief

#### Scenario: Approval rejected for non-submitted brief
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/upstream-actions?action=approve` when `downstream_state` is not "submitted"
- **THEN** the system returns a 409 error

### Requirement: Reject submitted brief
The system SHALL allow the creator to reject a submitted brief and force downstream to reopen it.

#### Scenario: Successful reject_submit
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/upstream-actions?action=reject_submit` with a required `content` rejection reason
- **THEN** the system sets `downstream_state` to "opened", leaves `upstream_state` as "in_process", updates `status_changed_at` / `status_changed_by`, creates a feedback record with `type` "reject_submit" and `is_to_down` true, and returns the updated brief

#### Scenario: Reject_submit rejected for non-submitted brief
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/upstream-actions?action=reject_submit` when `downstream_state` is not "submitted"
- **THEN** the system returns a 409 error

### Requirement: Push updated brief version
The system SHALL allow the creator to push a new version of an in-process brief, forcing downstream to reopen it.

#### Scenario: Successful update
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/upstream-actions?action=update` with new version fields and a required `content` change note
- **THEN** the system creates a new version, transitions it through draft → reviewed → sent, sets `briefs.current_version` to the new version, synchronizes `briefs.title` / `priority` / `expected_completion_at`, sets `downstream_state` to "opened", updates `status_changed_at` / `status_changed_by`, creates a feedback record with `type` "update" and `is_to_down` true, and returns the updated brief

#### Scenario: Update rejected for non-in-process brief
- **WHEN** the creator sends a POST request to `/api/v1/briefs/:brief_id/upstream-actions?action=update` when `upstream_state` is not "in_process"
- **THEN** the system returns a 409 error

### Requirement: Submit progress feedback
The system SHALL allow the assigned downstream user to submit a progress update without changing the brief state.

#### Scenario: Successful progress feedback
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/downstream-actions?action=process` with optional `content` and attachments
- **THEN** the system leaves `upstream_state` and `downstream_state` unchanged and creates a feedback record with `type` "progress" and `is_to_down` false

#### Scenario: Process rejected for non-assigned user
- **WHEN** a user other than `assigned_to` sends a POST request to `/api/v1/briefs/:brief_id/downstream-actions?action=process`
- **THEN** the system returns a 403 error

### Requirement: Submit completion
The system SHALL allow the assigned downstream user to submit completion of a brief.

#### Scenario: Successful submit
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/downstream-actions?action=submit` with a required `content` completion note and optional attachments
- **THEN** the system sets `downstream_state` to "submitted", updates `status_changed_at` / `status_changed_by`, and creates a feedback record with `type` "submit" and `is_to_down` false

#### Scenario: Submit rejected for non-in-process brief
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/downstream-actions?action=submit` when `upstream_state` is not "in_process"
- **THEN** the system returns a 409 error

### Requirement: Reopen brief
The system SHALL allow the assigned downstream user to reopen a brief from submitted, delegated, or blocked state.

#### Scenario: Successful open
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/downstream-actions?action=open` with a required `content` reopen reason
- **THEN** the system sets `downstream_state` to "opened", updates `status_changed_at` / `status_changed_by`, and creates a feedback record with `type` "open" and `is_to_down` false

#### Scenario: Open rejected for non-in-process brief
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/downstream-actions?action=open` when `upstream_state` is not "in_process"
- **THEN** the system returns a 409 error

### Requirement: Delegate brief
The system SHALL allow the assigned downstream user to mark a brief as delegated.

#### Scenario: Successful delegation
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/downstream-actions?action=delegate` with optional `content`
- **THEN** the system sets `downstream_state` to "delegated", updates `status_changed_at` / `status_changed_by`, and creates a feedback record with `type` "delegate" and `is_to_down` false

#### Scenario: Delegate rejected for non-in-process brief
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/downstream-actions?action=delegate` when `upstream_state` is not "in_process"
- **THEN** the system returns a 409 error

### Requirement: Block brief
The system SHALL allow the assigned downstream user to mark a brief as blocked.

#### Scenario: Successful block
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/downstream-actions?action=block` with a required `content` blocker reason and optional attachments
- **THEN** the system sets `downstream_state` to "blocked", updates `status_changed_at` / `status_changed_by`, and creates a feedback record with `type` "block" and `is_to_down` false

#### Scenario: Block rejected for non-in-process brief
- **WHEN** the assigned user sends a POST request to `/api/v1/briefs/:brief_id/downstream-actions?action=block` when `upstream_state` is not "in_process"
- **THEN** the system returns a 409 error
