## ADDED Requirements

### Requirement: Upstream can edit a draft brief
The system SHALL allow the brief creator to edit a brief when its status is `draft`.

#### Scenario: Successful edit
- **WHEN** the creator modifies title, content, priority, or estimated man days and saves
- **THEN** the system calls `PATCH /api/v1/briefs/[brief_id]`, refreshes the detail page, and shows the updated content

#### Scenario: Edit disabled for non-draft
- **WHEN** the creator views a brief whose status is not `draft`
- **THEN** the edit button is disabled or hidden

### Requirement: Upstream can send a reviewed brief to a downstream user
The system SHALL allow the brief creator to send a `reviewed` brief to another user.

#### Scenario: Send with user selection
- **WHEN** the creator clicks "发送给 downstream" and selects a user from the user selector
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/send` with `assigned_to` and an optional note, and transitions the brief status to `sent`

#### Scenario: Send disabled for non-reviewed
- **WHEN** the creator views a brief whose status is not `reviewed`
- **THEN** the send button is disabled or hidden

### Requirement: Downstream can accept a sent brief
The system SHALL allow the brief assignee to accept a `sent` brief.

#### Scenario: Accept brief
- **WHEN** the assignee clicks "接受"
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/accept`, refreshes the page, and shows the brief status as `accepted`

### Requirement: Downstream can reject a sent brief with a reason
The system SHALL allow the brief assignee to reject a `sent` brief and provide a reason.

#### Scenario: Reject with reason
- **WHEN** the assignee clicks "拒绝" and enters a rejection reason
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/reject` with the reason, refreshes the page, and shows the brief status as `draft`

#### Scenario: Reject without reason blocked
- **WHEN** the assignee tries to submit a rejection without entering a reason
- **THEN** the system displays a validation error and does not submit

### Requirement: Downstream can mark an accepted brief as done
The system SHALL allow the brief assignee to mark an `accepted` brief as `done` and provide a completion document.

#### Scenario: Complete with document
- **WHEN** the assignee clicks "标记完成" and enters completion notes
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/complete` and creates a `complete` feedback with the notes, then refreshes the page

### Requirement: Downstream can report a blocked brief
The system SHALL allow the brief assignee to report that an `accepted` brief is blocked and provide a reason.

#### Scenario: Blocked feedback with reason
- **WHEN** the assignee clicks "标记阻塞" and enters the blocked reason
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/feedbacks` with `type: "blocked"` and the reason, then refreshes the page

#### Scenario: Blocked without reason blocked
- **WHEN** the assignee tries to submit a blocked feedback without a reason
- **THEN** the system displays a validation error and does not submit
