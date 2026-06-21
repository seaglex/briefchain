## ADDED Requirements

### Requirement: Brief entity stores tree structure and lifecycle state
The system SHALL provide a `Brief` SQLAlchemy model that stores the brief identifier, root identifier, parent identifier, current version, status, creator, assignee, and timestamps.

#### Scenario: Create a root brief
- **WHEN** an upstream user creates a root brief
- **THEN** a `Brief` row is inserted with `parent_id` set to null, `root_id` equal to `brief_id`, `is_root` set to true, `current_version` set to 1, and `status` set to "draft"

#### Scenario: Create a child brief
- **WHEN** an upstream user creates a child brief under an existing brief
- **THEN** a `Brief` row is inserted with `parent_id` referencing the parent brief, `root_id` equal to the root brief identifier, and `is_root` set to false

### Requirement: Brief status uses a defined enumeration
The system SHALL restrict `Brief.status` to the values "draft", "reviewed", "sent", "accepted", "done", "blocked", and "cancelled".

#### Scenario: Invalid status is rejected
- **WHEN** code attempts to assign an unsupported value to `Brief.status`
- **THEN** the assignment is rejected by the `BriefStatus` enumeration

### Requirement: Brief relationships are navigable
The system SHALL define SQLAlchemy relationships from `Brief` to its parent, children, versions, transfer history, feedback, and chain.

#### Scenario: Load brief with children
- **WHEN** a brief with child briefs is queried
- **THEN** the `children` relationship returns the associated child `Brief` instances
