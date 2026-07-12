## ADDED Requirements

### Requirement: Trigger asynchronous review
The system SHALL expose `POST /api/v1/briefs/{brief_id}/reviews` to create an asynchronous review and enqueue it for worker processing.

#### Scenario: Valid submit-review request
- **WHEN** an upstream user calls `POST /api/v1/briefs/{brief_id}/reviews`
- **THEN** the system creates a `brief_arbiter_reviews` record with `status="processing"` and `attempt_count=0`, enqueues a review task, and returns HTTP 202 with `review_id` and `brief_version`

#### Scenario: Review already in progress
- **WHEN** a review request is received for a brief that already has a `processing` review
- **THEN** the system returns HTTP 409 with error code `REVIEW_ALREADY_IN_PROGRESS`

#### Scenario: Caller is not the brief creator
- **WHEN** a user who is not the brief's `created_by` calls the endpoint
- **THEN** the system returns HTTP 403

### Requirement: Query review status
The system SHALL expose `GET /api/v1/briefs/{brief_id}/reviews/{review_id}` to return the current review state.

#### Scenario: Review is processing
- **WHEN** the review has `status="processing"`
- **THEN** the endpoint returns HTTP 200 with `status`, `attempt_count`, and `created_at`

#### Scenario: Review has passed
- **WHEN** the review has `status="passed"`
- **THEN** the endpoint returns HTTP 200 with `score`, `issues`, `suggestions`, and `reviewed_at`

#### Scenario: Review has been rejected
- **WHEN** the review has `status="rejected"`
- **THEN** the endpoint returns HTTP 200 with `score`, `issues`, `suggestions`, and `reviewed_at`

#### Scenario: Review has failed
- **WHEN** the review has `status="failed"`
- **THEN** the endpoint returns HTTP 200 with `error` and `attempt_count`

### Requirement: Accept optional webhook URL
The system SHALL accept an optional `webhook_url` in the review creation request and persist it on the review record.

#### Scenario: Custom webhook provided
- **WHEN** the request body contains `webhook_url`
- **THEN** the system stores the URL in `brief_arbiter_reviews.webhook_url` and the worker uses it for notifications

#### Scenario: No webhook provided
- **WHEN** the request body does not contain `webhook_url`
- **THEN** the system uses the system default `ARBITER_WEBHOOK_URL` if configured
