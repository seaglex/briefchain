## ADDED Requirements

### Requirement: YAML metadata formatter shows key fields
The system SHALL provide a YAML formatter on the brief detail page that displays `title`, `priority`, `estimated_man_days`, and `expected_completion_at`.

#### Scenario: View brief detail
- **WHEN** a user opens the detail page of any brief
- **THEN** a YAML-formatted block showing the four fields is visible near the content area

### Requirement: YAML formatter handles missing values
The system SHALL display missing numeric or date values in the YAML formatter without rendering invalid YAML.

#### Scenario: View brief without estimated man days
- **WHEN** a user opens a brief that has no `estimated_man_days`
- **THEN** the YAML formatter shows the field as empty or omitted without breaking the layout
