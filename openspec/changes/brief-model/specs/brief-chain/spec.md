## ADDED Requirements

### Requirement: Brief chain metadata stores chain-level information
The system SHALL provide a `BriefChain` SQLAlchemy model that stores the chain identifier, title, owner identifier and name snapshot, priority, and timestamps.

#### Scenario: Create a root brief
- **WHEN** an upstream user creates a root brief
- **THEN** a `BriefChain` row is inserted with `chain_id` equal to the root brief identifier, `title` equal to the root brief title, `owner_id` equal to the root brief `created_by`, `owner_name` equal to the root brief `created_by_name`, and `priority` equal to the root brief priority

### Requirement: Chain priority uses a defined enumeration
The system SHALL restrict `BriefChain.priority` to the values "p0", "p1", "p2", and "p3".

#### Scenario: Invalid chain priority is rejected
- **WHEN** code attempts to assign an unsupported value to `BriefChain.priority`
- **THEN** the assignment is rejected by the `BriefPriority` enumeration

### Requirement: Chain membership is derived from briefs
The system SHALL not store explicit chain membership; membership is derived by querying `Brief` rows where `root_id` equals the chain identifier.

#### Scenario: List chain members
- **WHEN** the members of a chain are requested
- **THEN** the system returns all `Brief` rows with `root_id` equal to the requested chain identifier
