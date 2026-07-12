## ADDED Requirements

### Requirement: Worker runs as a background subprocess
The system SHALL start the Arbiter Worker as a subprocess when the FastAPI main process starts and terminate it gracefully on shutdown.

#### Scenario: FastAPI starts
- **WHEN** the FastAPI application starts
- **THEN** it spawns the worker subprocess using the same Python interpreter and virtual environment

#### Scenario: FastAPI receives shutdown signal
- **WHEN** the FastAPI main process receives SIGTERM or SIGINT
- **THEN** it forwards the signal to the worker and waits for it to shut down

### Requirement: Worker dispatches tasks by type
The worker SHALL read tasks from the queue and dispatch each task to a handler based on its `type`.

#### Scenario: Task type is review and SKIP_REVIEW is enabled
- **WHEN** the worker dequeues a task with `type="review"` and `SKIP_REVIEW=true`
- **THEN** it marks the review as `force_skipped` and sends a webhook notification without invoking the LLM

#### Scenario: Task type is review and SKIP_REVIEW is disabled
- **WHEN** the worker dequeues a task with `type="review"` and `SKIP_REVIEW` is not enabled
- **THEN** it invokes `ReviewHandler.execute(review)` to perform the LLM-based review

#### Scenario: Unknown task type
- **WHEN** the worker dequeues a task with an unsupported type
- **THEN** it logs the event and skips the task without re-enqueueing

### Requirement: Worker manages retries
The worker SHALL increment `attempt_count`, persist the last error, and re-enqueue tasks that fail with transient errors until `max_retries` is reached.

#### Scenario: Transient LLM failure below retry limit
- **WHEN** a review task fails due to an LLM timeout or rate limit and `attempt_count < max_retries`
- **THEN** the worker increments `attempt_count`, records the error, and re-enqueues the task

#### Scenario: Retry limit exceeded
- **WHEN** a review task fails and `attempt_count >= max_retries`
- **THEN** the worker sets the review status to `failed`, records the error, and sends a webhook notification

### Requirement: Worker performs health recovery
The worker SHALL periodically scan `brief_arbiter_reviews` for records stuck in `processing` beyond the configured timeout and re-enqueue them.

#### Scenario: Stuck review detected
- **WHEN** a review has `status="processing"` and `last_attempt_at` is older than `WORKER_PROCESSING_TIMEOUT`
- **THEN** the worker re-enqueues the review task

### Requirement: Worker notifies via webhook
The worker SHALL send a webhook notification after a review reaches a terminal state (`passed`, `rejected`, or `failed`).

#### Scenario: Review reaches terminal state
- **WHEN** a review status is updated to `passed`, `rejected`, or `failed`
- **THEN** the worker posts a webhook event to the configured URL after the database transaction commits

#### Scenario: Webhook delivery fails
- **WHEN** the webhook HTTP request fails
- **THEN** the worker logs the failure and continues processing without blocking the queue
