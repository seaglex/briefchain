## ADDED Requirements

### Requirement: Brief entity stores tree structure and dual lifecycle state
The system SHALL provide a `Brief` SQLAlchemy model that stores the brief identifier, root identifier, parent identifier, current sent version, upstream state, downstream state, denormalized title and priority, expected completion time, creator and assignee identifiers and name snapshots, state-change tracking with operator name snapshot, and timestamps.

#### Scenario: Create a root brief
- **WHEN** an upstream user creates a root brief
- **THEN** a `Brief` row is inserted with `parent_id` set to null, `root_id` equal to `brief_id`, `is_root` set to true, `current_version` set to null, `upstream_state` set to "editing", `downstream_state` set to null, `title` and `priority` copied from the initial version, `created_by` set to the upstream user id, and `created_by_name` set to the upstream user's name at creation time

#### Scenario: Create a child brief
- **WHEN** an upstream user creates a child brief under an existing brief
- **THEN** a `Brief` row is inserted with `parent_id` referencing the parent brief, `root_id` equal to the root brief identifier, and `is_root` set to false

### Requirement: Brief upstream state uses a defined enumeration
The system SHALL restrict `Brief.upstream_state` to the values "editing", "sent", "in_process", "suspended", "cancelled", and "done".

#### Scenario: Invalid upstream state is rejected
- **WHEN** code attempts to assign an unsupported value to `Brief.upstream_state`
- **THEN** the assignment is rejected by the `BriefUpstreamState` enumeration

### Requirement: Brief downstream state uses a defined enumeration
The system SHALL restrict `Brief.downstream_state` to the values "opened", "delegated", "blocked", and "submitted", and SHALL allow it to be null when `upstream_state` is not "in_process".

#### Scenario: Invalid downstream state is rejected
- **WHEN** code attempts to assign an unsupported value to `Brief.downstream_state`
- **THEN** the assignment is rejected by the `BriefDownstreamState` enumeration

### Requirement: Brief priority uses a defined enumeration
The system SHALL restrict `Brief.priority` to the values "p0", "p1", "p2", and "p3".

#### Scenario: Invalid priority is rejected
- **WHEN** code attempts to assign an unsupported value to `Brief.priority`
- **THEN** the assignment is rejected by the `BriefPriority` enumeration

### Requirement: Brief stores creator and assignee name snapshots
The system SHALL store `created_by_name` and `assigned_to_name` as the user's name at the time the brief is created or assigned, respectively.

#### Scenario: Assign a downstream user
- **WHEN** an upstream user assigns a brief to a downstream user
- **THEN** `assigned_to` is set to the downstream user id and `assigned_to_name` is set to the downstream user's name at assignment time

### Requirement: Brief tracks the last state change
The system SHALL store `status_changed_at`, `status_changed_by`, and `status_changed_by_name` to record when, by whom, and by what name the brief's state was last changed.

#### Scenario: Accept a sent brief
- **WHEN** a downstream user accepts a sent brief
- **THEN** `status_changed_at` is updated to the current time, `status_changed_by` is set to the downstream user's id, and `status_changed_by_name` is set to the downstream user's name at that time

### Requirement: Brief relationships are navigable
The system SHALL define SQLAlchemy relationships from `Brief` to its parent, children, versions, transfer history, feedback, chain, and arbiter reviews.

#### Scenario: Load brief with children
- **WHEN** a brief with child briefs is queried
- **THEN** the `children` relationship returns the associated child `Brief` instances
