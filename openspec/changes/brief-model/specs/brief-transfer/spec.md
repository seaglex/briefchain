## ADDED Requirements

### Requirement: Brief transfer history records brief lifecycle transitions
The system SHALL provide a `BriefTransferHistory` SQLAlchemy model mapped to the table `brief_transfer_history` that records the brief identifier, brief version, associated arbiter review, sender and receiver identifiers and name snapshots, sent time, accepted time, rejected time, and rejection reason.

#### Scenario: Send a brief
- **WHEN** an upstream user sends a reviewed brief to a downstream user
- **THEN** a `BriefTransferHistory` row is inserted with `sent_at` set to the current time and both `accepted_at` and `rejected_at` set to null

#### Scenario: Accept a brief
- **WHEN** the downstream user accepts a sent brief
- **THEN** the corresponding `BriefTransferHistory` row has `accepted_at` set to the current time

#### Scenario: Reject a brief
- **WHEN** the downstream user rejects a sent brief
- **THEN** the corresponding `BriefTransferHistory` row has `rejected_at` set to the current time and `rejection_reason` populated

### Requirement: Brief transfer history stores sender and receiver name snapshots
The system SHALL store `from_user_name` and `to_user_name` as the users' names at the time the transfer is created.

#### Scenario: Send a brief to a downstream user
- **WHEN** an upstream user sends a brief
- **THEN** `from_user_name` is set to the upstream user's current name and `to_user_name` is set to the downstream user's current name

### Requirement: Brief transfer history is linked to its brief
The system SHALL define a SQLAlchemy relationship from `BriefTransferHistory` to `Brief` and from `Brief` to its transfer records.

#### Scenario: List brief transfer history
- **WHEN** the transfer history of a brief is requested
- **THEN** the `transfers` relationship returns all associated `BriefTransferHistory` rows ordered by `sent_at` descending
