## ADDED Requirements

### Requirement: Review brief content using the brief-review skill
The system SHALL load the `brief-review` skill from `src/briefchain/skills/brief-review` using Google ADK and invoke it with the brief content as input.

#### Scenario: Skill is loaded and invoked for a review task
- **WHEN** a worker processes a `review` task
- **THEN** the system loads the `brief-review` skill and passes the brief content to the configured LLM

### Requirement: Evaluate brief across four dimensions
The system SHALL evaluate the brief against the four dimensions defined in the skill (Why, What, Goals, Hypothesis) and determine whether each dimension is present and reasonable.

#### Scenario: All four dimensions are present and reasonable
- **WHEN** the brief contains clear and reasonable Why, What, Goals, and Hypothesis sections
- **THEN** the review status SHALL be `passed`

#### Scenario: At least one dimension is missing or unreasonable
- **WHEN** the brief is missing a dimension or contains vague, unmeasurable, or ambiguous content
- **THEN** the review status SHALL be `rejected`

### Requirement: Produce structured review output
The system SHALL produce a structured result containing a numeric score, a list of issues, a list of suggestions, and the final passed/rejected verdict.

#### Scenario: Review completes successfully
- **WHEN** the LLM returns a structured review result
- **THEN** the system SHALL store `score`, `issues`, `suggestions`, and `reviewed_at` in the review record

### Requirement: Use configurable third-party LLM provider
The system SHALL read the LLM endpoint, model name, and API key from environment variables so that a third-party LLM API can be used.

#### Scenario: Environment variables are configured
- **WHEN** `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY` are set
- **THEN** the worker SHALL use those values when invoking the LLM for the review skill

### Requirement: Support SKIP_REVIEW bypass mode
The system SHALL support a `SKIP_REVIEW` environment variable that, when set to `true`, causes the worker to bypass the LLM skill and mark the review as `force_skipped`.

#### Scenario: SKIP_REVIEW is enabled
- **WHEN** `SKIP_REVIEW=true` and a review task is processed
- **THEN** the system SHALL NOT invoke the LLM, SHALL set `review.status = force_skipped`, and SHALL send a webhook notification

#### Scenario: SKIP_REVIEW is disabled
- **WHEN** `SKIP_REVIEW` is unset or not `true` and a review task is processed
- **THEN** the system SHALL invoke the LLM skill normally
