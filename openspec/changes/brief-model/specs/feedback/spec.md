## ADDED Requirements

### Requirement: Feedback stores downstream communication
The system SHALL provide a `Feedback` SQLAlchemy model that stores the feedback identifier, brief identifier, brief version, type, auto-generation flag, content, attachments, sender, creation time, confirmation time, and update time.

#### Scenario: Create progress feedback
- **WHEN** a downstream user submits progress feedback on an accepted brief
- **THEN** a `Feedback` row is inserted with `type` set to "progress" and `is_auto_generated` set to false

#### Scenario: Create blocked feedback
- **WHEN** a downstream user submits blocked feedback on an accepted brief
- **THEN** a `Feedback` row is inserted with `type` set to "blocked" and the brief status transitions to "blocked"

#### Scenario: Create completion feedback
- **WHEN** a downstream user submits completion feedback with evidence
- **THEN** a `Feedback` row is inserted with `type` set to "completion" and `content` containing evidence description

### Requirement: Feedback type uses a defined enumeration
The system SHALL restrict `Feedback.type` to the values "blocked", "progress", and "completion".

#### Scenario: Invalid feedback type is rejected
- **WHEN** code attempts to assign an unsupported value to `Feedback.type`
- **THEN** the assignment is rejected by the `FeedbackType` enumeration

### Requirement: Auto-generated feedback requires confirmation
The system SHALL store `confirmed_at` for auto-generated feedback and leave it null until a human confirms it.

#### Scenario: Confirm auto-generated feedback
- **WHEN** a downstream user confirms an auto-generated rollup feedback
- **THEN** the `Feedback.confirmed_at` field is set to the current time
