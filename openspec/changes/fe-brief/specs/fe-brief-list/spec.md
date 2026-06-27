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

### Requirement: Brief list supports upstream and downstream state filters
The system SHALL allow users to filter the brief list by `upstream_state` and `downstream_state`.

#### Scenario: Upstream state filter applied
- **WHEN** the user selects an upstream state from the upstream state dropdown
- **THEN** the system calls `GET /api/v1/briefs?role=<role>&upstream_state=<upstream_state>` and displays only matching briefs

#### Scenario: Downstream state filter applied
- **WHEN** the user selects a downstream state from the downstream state dropdown
- **THEN** the system calls `GET /api/v1/briefs?role=<role>&downstream_state=<downstream_state>` and displays only matching briefs

#### Scenario: Combined state filters applied
- **WHEN** the user selects both an upstream state and a downstream state
- **THEN** the system calls `GET /api/v1/briefs?role=<role>&upstream_state=<upstream_state>&downstream_state=<downstream_state>` and displays only matching briefs

#### Scenario: Clear state filters
- **WHEN** the user clears the state dropdowns
- **THEN** the system calls `GET /api/v1/briefs?role=<role>` without state filters

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
- **THEN** each card displays title, priority badge, upstream state badge, downstream state badge when present, and assignee information
