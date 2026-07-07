## ADDED Requirements

### Requirement: Landing page displays product slogans
The system SHALL provide a dedicated landing page that displays the three product slogans with titles and short descriptions.

#### Scenario: User visits landing page
- **WHEN** a user navigates to the landing page
- **THEN** the page shows the three slogans: "团队间以 brief 转移为工作天然分界", "平等对待上下游", and "全链路透明闭环"

### Requirement: Login page shows slogans below the form
The system SHALL display the product slogans below the login form on the login page.

#### Scenario: User opens login page
- **WHEN** a user visits the login page
- **THEN** the slogans section is visible below the login card

### Requirement: Register page shows slogans below the form
The system SHALL display the product slogans below the registration form on the register page.

#### Scenario: User opens register page
- **WHEN** a user visits the register page
- **THEN** the slogans section is visible below the registration card

### Requirement: Invite page shows slogans below the invite content
The system SHALL display the product slogans below the invite content on the invite page.

#### Scenario: User opens invite page
- **WHEN** a user visits an invite page
- **THEN** the slogans section is visible below the invite details and actions

### Requirement: Brand link points to landing page
The system SHALL make the BriefChain brand link in the top-left corner navigate to the landing page.

#### Scenario: User clicks brand link from any internal page
- **WHEN** a logged-in user clicks the BriefChain logo/brand in the top-left corner
- **THEN** the browser navigates to the landing page

### Requirement: Slogans are rendered consistently
The system SHALL render the slogans using a shared component so that login, register, and invite pages share the same layout and styling.

#### Scenario: Slogans appear on multiple pages
- **WHEN** the slogans are shown on login, register, and invite pages
- **THEN** they use the same component and visual style
