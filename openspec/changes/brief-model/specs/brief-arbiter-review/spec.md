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
