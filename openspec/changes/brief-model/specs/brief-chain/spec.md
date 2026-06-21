## ADDED Requirements

### Requirement: Brief chain metadata stores chain-level information
The system SHALL provide a `BriefChain` SQLAlchemy model that stores the chain identifier, title, and timestamps.

#### Scenario: Create a root brief
- **WHEN** an upstream user creates a root brief
- **THEN** a `BriefChain` row is inserted with `chain_id` equal to the root brief identifier and `title` equal to the root brief title

### Requirement: Chain membership is derived from briefs
The system SHALL not store explicit chain membership; membership is derived by querying `Brief` rows where `root_id` equals the chain identifier.

#### Scenario: List chain members
- **WHEN** the members of a chain are requested
- **THEN** the system returns all `Brief` rows with `root_id` equal to the requested chain identifier
