## ADDED Requirements

### Requirement: Public invite page has a dedicated header
The invite page SHALL render a top header without the application's left sidebar.

#### Scenario: Header is rendered
- **WHEN** a recipient opens `/invites/{token}`
- **THEN** the page shows the BriefChain icon and name in the top-left
- **AND** displays the tagline "AI-reviewed briefs for smoother handoffs"
- **AND** shows the recipient's name, a welcome message, and login/register links

### Requirement: Public invite page displays the Brief detail
The invite page SHALL display the Brief details using the same component as the authenticated Brief detail page.

#### Scenario: Brief detail is shown
- **WHEN** the invite token is valid and the invite has not expired
- **THEN** the page renders the Brief detail view below the header
- **AND** the Brief detail matches the data returned by `GET /invites/{token}`

### Requirement: Public invite page hides creator-only actions
The Brief detail component on the invite page SHALL hide actions that are only relevant to the creator, such as edit, review, send, cancel, suspend, resume, approve, reject_submit, and update.

#### Scenario: Creator actions are hidden
- **WHEN** the Brief detail is rendered in invite view mode
- **THEN** creator-only buttons are not visible
- **AND** recipient action controls (accept, reject, submit, block, open, delegate) are rendered separately by the invite page

### Requirement: Public invite page supports transfer-phase actions
The system SHALL allow the recipient to accept or reject the brief while `upstream_state` is "sent".

#### Scenario: Accept invite
- **WHEN** the recipient clicks "接受"
- **THEN** the system calls the token-based accept endpoint, refreshes the brief, and shows `upstream_state` as "in_process" and `downstream_state` as "opened"

#### Scenario: Reject invite
- **WHEN** the recipient clicks "拒绝" and enters a reason
- **THEN** the system calls the token-based reject endpoint, refreshes the brief, and shows `upstream_state` as "editing"

### Requirement: Public invite page supports downstream actions
The system SHALL allow the recipient to perform downstream actions after accepting the brief.

#### Scenario: Submit completion
- **WHEN** the recipient clicks "提交完成" and enters completion notes
- **THEN** the system calls the token-based submit endpoint, refreshes the brief, and shows `downstream_state` as "submitted"

#### Scenario: Block brief
- **WHEN** the recipient clicks "标记阻塞" and enters a blocker reason
- **THEN** the system calls the token-based block endpoint, refreshes the brief, and shows `downstream_state` as "blocked"

### Requirement: Invalid or expired invites show an error
The invite page SHALL display a clear error when the token is invalid, expired, or invalidated.

#### Scenario: Expired invite
- **WHEN** the invite token has passed its accept deadline
- **THEN** the page shows an "Invite expired" message
- **AND** provides a link to the login page

#### Scenario: Invalidated invite
- **WHEN** the temporary user has already registered or logged in
- **THEN** the page shows an "Invite invalidated" message
- **AND** provides a link to the login page
