## ADDED Requirements

### Requirement: Feedback stores formal contract notifications
The system SHALL provide a `Feedback` SQLAlchemy model that stores the feedback identifier, brief identifier, brief version, direction flag, type, content, attachments, sender and receiver identifiers and name snapshots, auto-generation flag, confirmation time, and timestamps.

#### Scenario: Create progress feedback
- **WHEN** a downstream user submits a progress update on a brief
- **THEN** a `Feedback` row is inserted with `is_to_down` set to false, `type` set to "progress", and `is_auto_generated` set to false

#### Scenario: Create block feedback
- **WHEN** a downstream user submits blocked feedback on an in-process brief
- **THEN** a `Feedback` row is inserted with `is_to_down` set to false, `type` set to "block", `content` containing the blocker reason, and the brief's `downstream_state` transitions to "blocked"

#### Scenario: Create submit feedback
- **WHEN** a downstream user submits completion feedback with evidence
- **THEN** a `Feedback` row is inserted with `is_to_down` set to false, `type` set to "submit", and `content` containing the completion evidence

#### Scenario: Create approve feedback
- **WHEN** an upstream user approves a submitted brief
- **THEN** a `Feedback` row is inserted with `is_to_down` set to true, `type` set to "approve", and the brief's `upstream_state` transitions to "done" and `downstream_state` to null

#### Scenario: Create update feedback
- **WHEN** an upstream user pushes a new brief version downstream
- **THEN** a `Feedback` row is inserted with `is_to_down` set to true, `type` set to "update", the new version becomes the current final version, and the brief's `downstream_state` transitions to "opened"

### Requirement: Feedback type uses a defined enumeration
The system SHALL restrict `Feedback.type` based on `is_to_down`: when `is_to_down` is true the values are "cancel", "suspend", "resume", "approve", "reject_submit", and "update"; when `is_to_down` is false the values are "submit", "block", "delegate", "open", and "progress".

#### Scenario: Invalid feedback type is rejected
- **WHEN** code attempts to assign an unsupported value to `Feedback.type`
- **THEN** the assignment is rejected by the `FeedbackType` enumeration

### Requirement: Feedback stores sender and receiver name snapshots
The system SHALL store `from_user_name` and `to_user_name` as the users' names at the time the feedback is created.

#### Scenario: Send feedback
- **WHEN** a user sends feedback
- **THEN** `from_user_name` is set to the sender's current name and `to_user_name` is set to the receiver's current name

### Requirement: Auto-generated feedback requires confirmation
The system SHALL store `confirmed_at` for auto-generated feedback and leave it null until a human confirms it.

#### Scenario: Confirm auto-generated feedback
- **WHEN** a downstream user confirms an auto-generated rollup feedback
- **THEN** the `Feedback.confirmed_at` field is set to the current time
