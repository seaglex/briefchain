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
The Brief detail component on the invite page SHALL hide actions that are only relevant to the creator, such as send, edit, or submit.

#### Scenario: Creator actions are hidden
- **WHEN** the Brief detail is rendered in invite view mode
- **THEN** send, edit, and submit buttons are not visible
- **AND** accept, reject, block, and complete action controls are rendered separately by the invite page

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
