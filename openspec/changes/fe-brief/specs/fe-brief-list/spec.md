## ADDED Requirements

### Requirement: Brief list page renders with role tabs
The system SHALL provide a Brief list page at `/briefs` that displays tabs for "我创建的" and "分配给我的".

#### Scenario: Default landing
- **WHEN** an authenticated user navigates to `/` or `/briefs`
- **THEN** the system redirects to or renders `/briefs?role=assigned`

#### Scenario: Tab switching
- **WHEN** the user clicks the "我创建的" tab
- **THEN** the URL becomes `/briefs?role=created` and the list refreshes to show only briefs created by the current user

#### Scenario: Click brief item
- **WHEN** the user clicks a brief card in the list
- **THEN** the system navigates to `/briefs/[brief_id]`

### Requirement: Brief list supports status filter
The system SHALL allow users to filter the brief list by status when the backend API supports it.

#### Scenario: Status filter applied
- **WHEN** the user selects a status from the status dropdown
- **THEN** the system calls `GET /api/v1/briefs?role=<role>&status=<status>` and displays only matching briefs

#### Scenario: Clear status filter
- **WHEN** the user clears the status dropdown
- **THEN** the system calls `GET /api/v1/briefs?role=<role>` without a status filter

### Requirement: Brief list supports priority filter on loaded data
The system SHALL allow users to filter the currently loaded brief list by priority when priority is not supported by the backend list API.

#### Scenario: Priority filter applied
- **WHEN** the user selects a priority from the priority dropdown
- **THEN** the system hides briefs whose priority does not match the selected value

#### Scenario: Clear priority filter
- **WHEN** the user clears the priority dropdown
- **THEN** the system shows all loaded briefs again

### Requirement: List page matches prototype style
The system SHALL render brief cards using the visual style from `04-frontend-prototype.html`.

#### Scenario: Brief card rendering
- **WHEN** the list page loads with briefs
- **THEN** each card displays title, priority badge, status badge, and assignee information
