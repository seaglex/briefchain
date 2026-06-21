## ADDED Requirements

### Requirement: Create brief page renders a form
The system SHALL provide a page at `/briefs/new` that allows an authenticated user to create a new Brief.

#### Scenario: Create brief page loads
- **WHEN** an authenticated user navigates to `/briefs/new`
- **THEN** the page displays a form with fields for title, content, priority, and estimated man days

### Requirement: Create brief form validates required fields
The system SHALL validate that title and content are non-empty before submission.

#### Scenario: Submit with empty title
- **WHEN** the user clicks "创建" without entering a title
- **THEN** the system displays a validation error and does not submit the form

#### Scenario: Submit with empty content
- **WHEN** the user clicks "创建" without entering content
- **THEN** the system displays a validation error and does not submit the form

### Requirement: Create brief submits to backend API
The system SHALL call `POST /api/v1/briefs` to create a new Brief.

#### Scenario: Successful creation
- **WHEN** the user enters valid title, content, priority, and estimated man days and clicks "创建"
- **THEN** the system calls `POST /api/v1/briefs` and redirects the user to the new Brief's detail page

#### Scenario: Failed creation
- **WHEN** the backend returns an error during creation
- **THEN** the system displays the error message and does not redirect

### Requirement: Create brief page matches prototype style
The system SHALL render the create brief form using the visual style from `04-frontend-prototype.html`.

#### Scenario: Form styling
- **WHEN** the create brief page loads
- **THEN** the form uses BriefChain card, input, button, and badge styles
