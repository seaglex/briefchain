## ADDED Requirements

### Requirement: Upstream can patch a brief in editing state
The system SHALL allow the brief creator to patch a brief when `upstream_state` is "editing".

#### Scenario: Successful patch
- **WHEN** the creator modifies title, content, priority, expected completion time, or estimated man days and saves
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/editing?action=patch`, refreshes the detail page, and shows the updated content

#### Scenario: Patch disabled for non-editing state
- **WHEN** the creator views a brief whose `upstream_state` is not "editing"
- **THEN** the patch/edit button is disabled or hidden

### Requirement: Upstream can submit the current draft version for review
The system SHALL allow the brief creator to submit the current draft version for review.

#### Scenario: Successful review submission
- **WHEN** the creator clicks "提交审查"
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/editing?action=review`, refreshes the page, and shows the current version status as "reviewed"

#### Scenario: Review disabled when current version is not draft
- **WHEN** the creator views a brief whose current version status is not "draft"
- **THEN** the review button is disabled or hidden

### Requirement: Upstream can send a reviewed brief to a downstream user
The system SHALL allow the brief creator to send a reviewed brief to another user.

#### Scenario: Send to registered user
- **WHEN** the creator clicks "发送给 downstream" and selects a user from the user selector
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/transfer?action=send` with `is_temporary_user` false, `assigned_to`, and an optional note, and transitions the brief `upstream_state` to "sent"

#### Scenario: Send to temporary user
- **WHEN** the creator chooses "Temporary user", enters recipient information, and submits
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/transfer?action=send` with `is_temporary_user` true and the recipient details, and displays the returned invite link

#### Scenario: Send disabled for non-reviewed version
- **WHEN** the creator views a brief whose current version status is not "reviewed"
- **THEN** the send button is disabled or hidden

### Requirement: Downstream can accept or reject a sent brief
The system SHALL allow the brief assignee to accept or reject a sent brief.

#### Scenario: Accept brief
- **WHEN** the assignee clicks "接受"
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/transfer?action=accept` with an optional note, refreshes the page, and shows `upstream_state` as "in_process" and `downstream_state` as "opened"

#### Scenario: Reject with reason
- **WHEN** the assignee clicks "拒绝" and enters a rejection reason
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/transfer?action=reject` with the reason, refreshes the page, and shows `upstream_state` as "editing"

#### Scenario: Reject without reason blocked
- **WHEN** the assignee tries to submit a rejection without entering a reason
- **THEN** the system displays a validation error and does not submit

### Requirement: Upstream can cancel a brief
The system SHALL allow the brief creator to cancel a brief that is not already terminal.

#### Scenario: Successful cancellation
- **WHEN** the creator clicks "取消合约" and enters a cancellation reason
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/upstream-actions?action=cancel` with the reason, refreshes the page, and shows `upstream_state` as "cancelled"

### Requirement: Upstream can suspend and resume a brief
The system SHALL allow the brief creator to suspend and later resume an in-process or sent brief.

#### Scenario: Successful suspension
- **WHEN** the creator clicks "暂停" and enters a suspension reason
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/upstream-actions?action=suspend` with the reason, refreshes the page, and shows `upstream_state` as "suspended"

#### Scenario: Successful resume
- **WHEN** the creator clicks "恢复" and enters a resume reason
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/upstream-actions?action=resume` with the reason, refreshes the page, and shows `upstream_state` as "in_process"

### Requirement: Upstream can approve a submitted brief
The system SHALL allow the brief creator to approve a brief only when `downstream_state` is "submitted".

#### Scenario: Successful approval
- **WHEN** the creator clicks "验收通过" and enters an acceptance note
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/upstream-actions?action=approve` with the note, refreshes the page, and shows `upstream_state` as "done" and `downstream_state` as null

### Requirement: Upstream can reject a submitted brief
The system SHALL allow the brief creator to reject a submitted brief and force downstream to reopen it.

#### Scenario: Successful reject_submit
- **WHEN** the creator clicks "打回" and enters a rejection reason
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/upstream-actions?action=reject_submit` with the reason, refreshes the page, and shows `downstream_state` as "opened"

### Requirement: Upstream can push an updated brief version
The system SHALL allow the brief creator to push a new version of an in-process brief.

#### Scenario: Successful update
- **WHEN** the creator clicks "推送更新", enters new version fields, and provides a change note
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/upstream-actions?action=update` with the fields and note, refreshes the page, and shows a new `current_version` and `downstream_state` as "opened"

### Requirement: Downstream can submit progress feedback
The system SHALL allow the brief assignee to submit a progress update without changing the brief state.

#### Scenario: Successful progress feedback
- **WHEN** the assignee clicks "进度更新" and enters optional content and attachments
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/downstream-actions?action=process`, refreshes the page, and shows the new progress feedback in the feedback list

### Requirement: Downstream can submit completion
The system SHALL allow the brief assignee to submit completion of an in-process brief.

#### Scenario: Successful submit
- **WHEN** the assignee clicks "提交完成" and enters completion notes and optional attachments
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/downstream-actions?action=submit` with the notes, refreshes the page, and shows `downstream_state` as "submitted"

### Requirement: Downstream can reopen a brief
The system SHALL allow the brief assignee to reopen a brief from submitted, delegated, or blocked state.

#### Scenario: Successful open
- **WHEN** the assignee clicks "重开" and enters a reopen reason
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/downstream-actions?action=open` with the reason, refreshes the page, and shows `downstream_state` as "opened"

### Requirement: Downstream can delegate a brief
The system SHALL allow the brief assignee to mark a brief as delegated.

#### Scenario: Successful delegation
- **WHEN** the assignee clicks "委派" and optionally enters delegation notes
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/downstream-actions?action=delegate` with the notes, refreshes the page, and shows `downstream_state` as "delegated"

### Requirement: Downstream can block a brief
The system SHALL allow the brief assignee to mark a brief as blocked.

#### Scenario: Block with reason
- **WHEN** the assignee clicks "标记阻塞" and enters the blocked reason
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/downstream-actions?action=block` with the reason, refreshes the page, and shows `downstream_state` as "blocked"

#### Scenario: Block without reason blocked
- **WHEN** the assignee tries to submit a block without a reason
- **THEN** the system displays a validation error and does not submit
