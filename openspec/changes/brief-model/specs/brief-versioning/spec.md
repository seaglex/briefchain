## ADDED Requirements

### Requirement: Brief version stores a full content snapshot
The system SHALL provide a `BriefVersion` SQLAlchemy model that stores the brief identifier, version number, title, content, attachments, priority, estimated man-days, change flags, modifier, and timestamps.

#### Scenario: Create initial version
- **WHEN** a brief is created
- **THEN** a `BriefVersion` row is inserted with `version` equal to 1, `is_upstream_changed` set to false, and `revision_reason` set to "initial"

#### Scenario: Update brief content creates a new version
- **WHEN** an upstream user updates the title or content of a draft brief
- **THEN** a new `BriefVersion` row is inserted with `version` equal to `current_version + 1` and `Brief.current_version` is incremented

### Requirement: Brief version priority uses a defined enumeration
The system SHALL restrict `BriefVersion.priority` to the values "p0", "p1", "p2", and "p3".

#### Scenario: Invalid priority is rejected
- **WHEN** code attempts to assign an unsupported value to `BriefVersion.priority`
- **THEN** the assignment is rejected by the `BriefPriority` enumeration

### Requirement: Brief version is linked to its brief
The system SHALL define a SQLAlchemy relationship from `BriefVersion` to `Brief` and from `Brief` to its ordered versions.

#### Scenario: List brief versions
- **WHEN** the versions of a brief are requested
- **THEN** the `versions` relationship returns `BriefVersion` rows ordered by ascending version number
