## ADDED Requirements

### Requirement: Creator can choose to send a Brief to a temporary user
The Brief send dialog SHALL provide an option to send the Brief to a temporary (external) user in addition to sending to an existing registered user.

#### Scenario: Temporary user option is visible
- **WHEN** the creator opens the send dialog from the Brief detail page
- **THEN** the dialog displays a choice between "Registered user" and "Temporary user"

### Requirement: Creator enters recipient information for temporary user
The system SHALL collect the recipient's name and an optional email or phone number before sending to a temporary user.

#### Scenario: Valid temporary user form
- **WHEN** the creator selects "Temporary user"
- **AND** enters a non-empty recipient name
- **AND** optionally enters an email or phone number
- **THEN** the send action becomes enabled

#### Scenario: Name is required
- **WHEN** the creator selects "Temporary user"
- **AND** leaves the recipient name empty
- **THEN** the send action is disabled

### Requirement: System generates and displays an invite link
After sending to a temporary user, the system SHALL display the invite link returned by the backend and allow the creator to copy it.

#### Scenario: Successful send to temporary user
- **WHEN** the creator submits the temporary user send form
- **THEN** the system calls `POST /api/v1/briefs/[brief_id]/transfer?action=send` with `is_temporary_user` true and the recipient details
- **AND** the backend returns an invite URL
- **THEN** the dialog shows the invite link
- **AND** the creator can copy the link to the clipboard

#### Scenario: Copy invite link
- **WHEN** the creator clicks the copy button next to the invite link
- **THEN** the link is written to the clipboard
- **AND** the UI indicates the copy succeeded
