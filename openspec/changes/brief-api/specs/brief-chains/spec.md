## ADDED Requirements

### Requirement: List chains
The system SHALL return a paginated list of brief chains accessible to the current user.

#### Scenario: Successful chain list
- **WHEN** an authenticated user sends a GET request to `/api/v1/chains`
- **THEN** the system returns chains with `chain_id`, `title`, `owner_id`, `owner_name`, `priority`, `root_brief_id`, `brief_count`, and `created_at`

#### Scenario: Empty chain list
- **WHEN** an authenticated user sends a GET request to `/api/v1/chains` and no chains exist
- **THEN** the system returns an empty list

### Requirement: Get chain detail
The system SHALL return the detail of a chain including its root brief and tree structure.

#### Scenario: Successful chain detail
- **WHEN** an authenticated user sends a GET request to `/api/v1/chains/:chain_id`
- **THEN** the system returns the chain metadata, the root brief in detail mode, and the full brief tree where each node contains `brief_id`, `title`, `upstream_state`, `downstream_state`, and `children`

#### Scenario: Chain not found
- **WHEN** an authenticated user sends a GET request to `/api/v1/chains/:chain_id` for a non-existent chain
- **THEN** the system returns a 404 error
