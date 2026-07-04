## ADDED Requirements

### Requirement: User can list comments on a task
The system SHALL return a cursor-paginated list of comments for a given task, ordered newest first, excluding comments on soft-deleted tasks.

#### Scenario: List comments
- **WHEN** an authenticated user sends `GET /tasks/:task_id/comments`
- **THEN** the system returns the comments with `created_by`, `created_by_name`, and `next_cursor`

### Requirement: User can create a comment on a task
The system SHALL allow any authenticated user to add a comment to an existing, non-deleted task. The creator's `user_id` and name SHALL be captured from the JWT token.

#### Scenario: Create comment
- **WHEN** an authenticated user sends `POST /tasks/:task_id/comments` with `content`
- **THEN** the system creates the comment and returns HTTP 201 with the comment object

### Requirement: Only the comment creator can update a comment
The system SHALL allow a comment's `created_by` user to edit its `content` and `updated_at`.

#### Scenario: Creator edits comment
- **WHEN** the comment creator sends `PUT /comments/:comment_id` with new `content`
- **THEN** the system returns HTTP 200 with the updated comment

#### Scenario: Non-creator cannot edit
- **WHEN** a user other than the creator sends `PUT /comments/:comment_id`
- **THEN** the system returns HTTP 403 with code `FORBIDDEN`

### Requirement: Only the comment creator can delete a comment
The system SHALL allow a comment's creator to delete it permanently.

#### Scenario: Creator deletes comment
- **WHEN** the comment creator sends `DELETE /comments/:comment_id`
- **THEN** the system removes the comment and returns HTTP 204

#### Scenario: Non-creator cannot delete
- **WHEN** a user other than the creator sends `DELETE /comments/:comment_id`
- **THEN** the system returns HTTP 403 with code `FORBIDDEN`
