## ADDED Requirements

### Requirement: User selector loads available users
The system SHALL provide a user selector that loads users from the backend user list API.

#### Scenario: Selector opens
- **WHEN** the user opens the user selector (e.g., in the send brief dialog)
- **THEN** the system calls `GET /api/v1/users` and displays the list of user names

### Requirement: User selector allows selecting a single user
The system SHALL allow the user to select exactly one user from the selector.

#### Scenario: User selected
- **WHEN** the user clicks a user in the selector
- **THEN** the selected user's id is captured and the selector shows the selected user

#### Scenario: Confirm selection
- **WHEN** the user confirms the selection
- **THEN** the selector closes and the calling action (e.g., send brief) receives the selected user id

### Requirement: User selector handles empty state
The system SHALL display an empty state when no users are available.

#### Scenario: No users
- **WHEN** the user list API returns no users
- **THEN** the selector displays a message indicating no users are available
