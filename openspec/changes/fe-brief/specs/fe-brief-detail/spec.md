## ADDED Requirements

### Requirement: Brief detail page displays brief content
The system SHALL provide a Brief detail page at `/briefs/[brief_id]` that shows the brief's current version content and metadata.

#### Scenario: Detail page loads
- **WHEN** an authenticated user navigates to `/briefs/[brief_id]`
- **THEN** the page displays the brief title, status badge, priority badge, content, creator, assignee, and timestamps

### Requirement: Detail page provides tabbed sections
The system SHALL provide tabs on the detail page for content, attachments, transfers, and feedbacks.

#### Scenario: Switch tabs
- **WHEN** the user clicks the "流转" tab
- **THEN** the page displays the brief's transfer history timeline

#### Scenario: View feedbacks
- **WHEN** the user clicks the "Feedback" tab
- **THEN** the page displays the list of feedbacks for the brief

### Requirement: Detail page shows role-aware action buttons
The system SHALL display action buttons based on the current user's relationship to the brief and the brief's status.

#### Scenario: Upstream view
- **WHEN** the current user is the brief creator and the brief status is `draft` or `reviewed`
- **THEN** the page shows upstream actions such as edit and send

#### Scenario: Downstream view
- **WHEN** the current user is the brief assignee and the brief status is `sent` or `accepted`
- **THEN** the page shows downstream actions such as accept, reject, complete, or blocked feedback

#### Scenario: Read-only view
- **WHEN** the current user is neither the creator nor the assignee
- **THEN** the page hides all action buttons and shows only content and history
