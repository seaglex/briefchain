## ADDED Requirements

### Requirement: submit-review triggers asynchronous review
The system SHALL change the `submit-review` upstream action from a synchronous force-skip to an asynchronous review trigger.

#### Scenario: Upstream submits a brief for review
- **WHEN** the upstream user calls `POST /api/v1/briefs/{brief_id}/editing?action=submit-review`
- **THEN** the system performs the duplicate-processing check, creates a review record, enqueues the review task, and returns HTTP 202

### Requirement: Only passed briefs can be sent
The system SHALL prevent `send` action on a brief whose latest review is not `passed`.

#### Scenario: Brief review passed
- **WHEN** the upstream user attempts to send a brief whose latest review has `status="passed"`
- **THEN** the send action succeeds

#### Scenario: Brief review rejected or failed
- **WHEN** the upstream user attempts to send a brief whose latest review has `status="rejected"` or `"failed"`
- **THEN** the send action is rejected with a clear error indicating the brief must be reviewed first

### Requirement: Resubmit after rejection
The system SHALL allow a new review to be triggered after the brief content is modified, even if a previous review was rejected.

#### Scenario: User patches and resubmits
- **WHEN** the brief is in `editing` state and the upstream user calls `submit-review` again after a previous `rejected` review
- **THEN** the system creates a new `processing` review and enqueues it
