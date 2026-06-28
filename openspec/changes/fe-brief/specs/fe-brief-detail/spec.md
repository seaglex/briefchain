## ADDED Requirements

### Requirement: Brief detail page displays brief content
The system SHALL provide a Brief detail page at `/briefs/[brief_id]` that shows the brief's current version content and metadata.

#### Scenario: Detail page loads
- **WHEN** an authenticated user navigates to `/briefs/[brief_id]`
- **THEN** the page displays the brief title, upstream state badge, downstream state badge when present, priority badge, content, creator name, assignee name, timestamps, and a `unsent_version` indicator when an editable draft exists

### Requirement: Detail page provides tabbed sections
The system SHALL provide tabs on the detail page for content, attachments, transfers, and feedbacks.

#### Scenario: Switch tabs
- **WHEN** the user clicks the "流转" tab
- **THEN** the page displays the brief's transfer history timeline

#### Scenario: View feedbacks
- **WHEN** the user clicks the "Feedback" tab
- **THEN** the page displays the list of feedbacks for the brief

### Requirement: Detail page shows role-aware action buttons
The system SHALL display action buttons based on the current user's relationship to the brief and the brief's upstream/downstream state combination.

#### Scenario: Upstream editing view
- **WHEN** the current user is the brief creator and `upstream_state` is "editing"
- **THEN** the page shows upstream actions such as edit and submit for review

#### Scenario: Draft version indicator shown
- **WHEN** the user views a brief where `unsent_version` is not `null`
- **THEN** the page displays a badge indicating "Draft v{N} available"
- **AND** the creator sees an edit button to load the draft version content

#### Scenario: Upstream can edit draft from sent or in_process state
- **WHEN** the current user is the brief creator, `upstream_state` is "sent" or "in_process", and `unsent_version` is not `null`
- **THEN** the page shows an edit button that loads the draft version content

#### Scenario: Downstream transfer view
- **WHEN** the current user is the brief assignee and `upstream_state` is "sent"
- **THEN** the page shows transfer actions to accept or reject the brief

#### Scenario: Downstream in-process view
- **WHEN** the current user is the brief assignee, `upstream_state` is "in_process", and `downstream_state` is "opened"
- **THEN** the page shows downstream actions such as delegate, block, and submit completion

#### Scenario: Downstream delegated view
- **WHEN** the current user is the brief assignee, `upstream_state` is "in_process", and `downstream_state` is "delegated"
- **THEN** the page shows downstream actions such as reopen, block, and submit completion

#### Scenario: Downstream submitted view
- **WHEN** the current user is the brief assignee, `upstream_state` is "in_process", and `downstream_state` is "submitted"
- **THEN** the page shows a downstream action to reopen the submission (open action)

#### Scenario: Upstream submitted view
- **WHEN** the current user is the brief creator, `upstream_state` is "in_process", and `downstream_state` is "submitted"
- **THEN** the page shows upstream actions such as approve, reject_submit, and push update

#### Scenario: Downstream blocked view
- **WHEN** the current user is the brief assignee, `upstream_state` is "in_process", and `downstream_state` is "blocked"
- **THEN** the page shows a downstream action to resolve the blocker by reopening or delegating

#### Scenario: Upstream suspended view
- **WHEN** the current user is the brief creator and `upstream_state` is "suspended"
- **THEN** the page shows upstream actions to resume or cancel the brief

#### Scenario: Read-only view
- **WHEN** the current user is neither the creator nor the assignee
- **THEN** the page hides all action buttons and shows only content and history
