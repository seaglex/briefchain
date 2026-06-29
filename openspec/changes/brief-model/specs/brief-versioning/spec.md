## ADDED Requirements

### Requirement: Brief version stores a full content snapshot and lifecycle status
The system SHALL provide a `BriefVersion` SQLAlchemy model that stores the brief identifier, version number, lifecycle status, title, content, attachments, priority, estimated man-days, expected completion time, associated arbiter review, upstream-change flag, revision reason, modifier identifier and name snapshot, modification time, change summary, and timestamps.

#### Scenario: Create initial version
- **WHEN** a brief is created
- **THEN** a `BriefVersion` row is inserted with `version` equal to 1, `status` set to "draft", `is_upstream_changed` set to false, `revision_reason` set to "initial", `modified_by` set to the upstream user's id, and `modified_by_name` set to the upstream user's name at creation time

#### Scenario: Update brief content creates a new draft version
- **WHEN** an upstream user updates the title or content of a draft brief
- **THEN** a new `BriefVersion` row is inserted with the next version number and `status` set to "draft"; `Brief.current_version` is not changed until the new version is finalized

#### Scenario: Send a version makes it the current version
- **WHEN** an upstream user sends a reviewed brief version downstream
- **THEN** the version's `status` becomes "final", `Brief.current_version` is updated to that version number, and `Brief.title`, `Brief.priority`, and `Brief.expected_completion_at` are synchronized to match that version

### Requirement: Brief version status uses a defined enumeration
The system SHALL restrict `BriefVersion.status` to the values "draft", "reviewed", and "final".

#### Scenario: Invalid version status is rejected
- **WHEN** code attempts to assign an unsupported value to `BriefVersion.status`
- **THEN** the assignment is rejected by the `BriefVersionStatus` enumeration

### Requirement: Brief version priority uses a defined enumeration
The system SHALL restrict `BriefVersion.priority` to the values "p0", "p1", "p2", and "p3".

#### Scenario: Invalid priority is rejected
- **WHEN** code attempts to assign an unsupported value to `BriefVersion.priority`
- **THEN** the assignment is rejected by the `BriefPriority` enumeration

### Requirement: Brief version records the effective arbiter review
The system SHALL store `arbiter_review_id` referencing the latest effective `BriefArbiterReview` for the version; `BriefTransferHistory` reads this value when the version is sent downstream without querying the reviews table again.

#### Scenario: Review a version before sending
- **WHEN** an arbiter review is recorded for a brief version
- **THEN** `arbiter_review_id` on the version points to that review and is used by the subsequent send action

### Requirement: Brief version is linked to its brief
The system SHALL define a SQLAlchemy relationship from `BriefVersion` to `Brief` and from `Brief` to its ordered versions.

#### Scenario: List brief versions
- **WHEN** the versions of a brief are requested
- **THEN** the `versions` relationship returns `BriefVersion` rows ordered by ascending version number
