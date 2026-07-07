## ADDED Requirements

### Requirement: Brief type is defined
The system SHALL support a `type` field on every brief with one of the following values: `idea`, `epic`, `feature`, `story`.

#### Scenario: Type enum is enforced
- **WHEN** a brief is created or updated with a `type` value
- **THEN** the system accepts only `idea`, `epic`, `feature`, or `story`

### Requirement: Brief defaults to idea type
The system SHALL default the brief `type` to `idea` when no type is provided.

#### Scenario: Create brief without type
- **WHEN** a user creates a brief without specifying `type`
- **THEN** the created brief has `type` equal to `idea`

#### Scenario: Existing briefs without type
- **WHEN** the system encounters a brief record that predates the `type` field
- **THEN** the brief is treated as having `type` equal to `idea`

### Requirement: Type is stored on brief and version
The system SHALL persist `type` on both the `briefs` table and the `brief_versions` table so that historical versions retain their original type.

#### Scenario: Version snapshot retains type
- **WHEN** a brief version is created
- **THEN** the version stores the `type` that was current at the time of the snapshot

### Requirement: Type is exposed in API responses
The system SHALL include `type` in brief list items and brief detail responses.

#### Scenario: List briefs
- **WHEN** a client requests the brief list endpoint
- **THEN** each returned brief contains a `type` field

#### Scenario: Get brief detail
- **WHEN** a client requests a single brief detail
- **THEN** the response contains a `type` field

### Requirement: Type is editable during creation and draft editing
The system SHALL allow users to set or change `type` when creating a brief or patching a draft version.

#### Scenario: Create brief with type
- **WHEN** a user creates a brief with `type` set to `feature`
- **THEN** the created brief has `type` equal to `feature`

#### Scenario: Patch draft type
- **WHEN** a user patches a draft brief and changes `type` to `story`
- **THEN** the draft version reflects the new `type`

### Requirement: Type is displayed in brief detail header
The system SHALL render the brief type in the brief detail page header before the title, formatted as `<Type> - Brief 详情`.

#### Scenario: View idea brief
- **WHEN** a user opens the detail page of a brief whose type is `idea`
- **THEN** the page header reads `Idea - Brief 详情`

#### Scenario: View feature brief
- **WHEN** a user opens the detail page of a brief whose type is `feature`
- **THEN** the page header reads `Feature - Brief 详情`

### Requirement: Type selector is shown in forms
The system SHALL provide a type selector in the brief creation form and the brief editing form.

#### Scenario: Create form includes type
- **WHEN** a user opens the brief creation form
- **THEN** a selector for `idea / epic / feature / story` is visible and defaults to `idea`

#### Scenario: Edit form includes type
- **WHEN** a user opens the brief editing form
- **THEN** the current type is pre-selected and can be changed
