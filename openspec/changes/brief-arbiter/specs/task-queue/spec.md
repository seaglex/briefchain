## ADDED Requirements

### Requirement: Enqueue a task
The system SHALL provide a `TaskQueue.enqueue(type, ref_id)` operation that inserts a record into the queue and returns a task identifier.

#### Scenario: Enqueue a review task
- **WHEN** the API calls `enqueue(type="review", ref_id=review.id)`
- **THEN** a new row is inserted into `task_queue` with the given type and ref_id

### Requirement: Dequeue the oldest task
The system SHALL provide a `TaskQueue.dequeue()` operation that atomically removes and returns the oldest pending task, ordered by creation time.

#### Scenario: Queue has pending tasks
- **WHEN** the worker calls `dequeue()`
- **THEN** the oldest `task_queue` row is deleted and returned

#### Scenario: Queue is empty
- **WHEN** the worker calls `dequeue()` and the queue is empty
- **THEN** the operation returns `null`

### Requirement: Queue backend abstraction
The system SHALL expose a backend-agnostic `TaskQueue` interface with a database implementation selected by configuration.

#### Scenario: Database backend is configured
- **WHEN** `QUEUE_BACKEND` is `database` or unset
- **THEN** the system uses `DatabaseTaskQueue` backed by the existing SQLAlchemy engine

### Requirement: Queue does not track task lifecycle
The queue SHALL store only task type, reference id, and creation time; status, retries, and results SHALL be managed by the business layer.

#### Scenario: Task is dequeued
- **WHEN** a task is returned from `dequeue()`
- **THEN** the task row is removed from the queue and no status column is updated
