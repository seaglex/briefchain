## ADDED Requirements

### Requirement: Feedback arbiter review records pre-send evaluation
The system SHALL provide a `FeedbackArbiterReview` SQLAlchemy model that stores the review identifier, feedback identifier, arbiter identifier, status, result, and timestamps.

#### Scenario: Completion review passes
- **WHEN** an arbiter reviews completion feedback and evidence is sufficient
- **THEN** a `FeedbackArbiterReview` row is inserted with `status` set to "passed" and `result["can_auto_done"]` set to true

#### Scenario: Completion review fails
- **WHEN** an arbiter reviews completion feedback and evidence is insufficient
- **THEN** a `FeedbackArbiterReview` row is inserted with `status` set to "failed" and `result["missing"]` populated

#### Scenario: Blocked review confirms blocker
- **WHEN** an arbiter reviews blocked feedback and confirms the blocker
- **THEN** a `FeedbackArbiterReview` row is inserted with `status` set to "passed" and `result["block_confirmed"]` set to true

### Requirement: Feedback arbiter review status uses a defined enumeration
The system SHALL restrict `FeedbackArbiterReview.status` to the values "passed", "failed", and "force_skipped".

#### Scenario: Invalid review status is rejected
- **WHEN** code attempts to assign an unsupported value to `FeedbackArbiterReview.status`
- **THEN** the assignment is rejected by the `ArbiterReviewStatus` enumeration
