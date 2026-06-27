## ADDED Requirements

### Requirement: Brief arbiter review records pre-send evaluation
The system SHALL provide a `BriefArbiterReview` SQLAlchemy model that stores the review identifier, brief identifier, brief version, arbiter identifier, status, score, issues, suggestions, and review time.

#### Scenario: Review passes
- **WHEN** an arbiter reviews a brief version and the quality is acceptable
- **THEN** a `BriefArbiterReview` row is inserted with `status` set to "passed" and a numeric score between 0 and 100

#### Scenario: Review fails
- **WHEN** an arbiter reviews a brief version and finds blockers
- **THEN** a `BriefArbiterReview` row is inserted with `status` set to "failed", `issues` populated with blocker details, and `suggestions` populated with improvement recommendations

#### Scenario: Review is force skipped
- **WHEN** an administrator bypasses the arbiter review
- **THEN** a `BriefArbiterReview` row is inserted with `status` set to "force_skipped"

### Requirement: Brief arbiter review status uses a defined enumeration
The system SHALL restrict `BriefArbiterReview.status` to the values "passed", "failed", and "force_skipped".

#### Scenario: Invalid review status is rejected
- **WHEN** code attempts to assign an unsupported value to `BriefArbiterReview.status`
- **THEN** the assignment is rejected by the `ArbiterReviewStatus` enumeration

### Requirement: Brief arbiter review issues follow a structured schema
The system SHALL store `issues` as a JSON list where each item contains `field`, `severity` ("blocker" | "major" | "minor"), and `message`.

#### Scenario: Review reports a blocker
- **WHEN** an arbiter review finds a blocker in the brief title
- **THEN** `issues` contains an object with `field` set to "title", `severity` set to "blocker", and a non-empty `message`

### Requirement: Brief arbiter review suggestions are a string list
The system SHALL store `suggestions` as a JSON list of strings.

#### Scenario: Review includes improvement suggestions
- **WHEN** an arbiter review produces improvement recommendations
- **THEN** `suggestions` is a non-empty list of strings
