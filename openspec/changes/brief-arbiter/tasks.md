## 1. Schema and Migrations

- [x] 1.1 Create migration for `task_queue` table (`id`, `type`, `ref_id`, `created_at`) with `idx_queue_fetch` index
- [x] 1.2 Create migration extending `brief_arbiter_reviews` with `status` enum updates, `attempt_count`, `last_attempt_at`, `error`, `webhook_url`
- [x] 1.3 Update `ArbiterReviewStatus` enum in `src/briefchain/models/enums.py` to include `processing`, `rejected`, `failed`
- [x] 1.4 Update `BriefArbiterReview` model in `src/briefchain/models/brief.py` with new columns and relationships

## 2. Configuration

- [x] 2.1 Add LLM configuration to `src/briefchain/api/config.py`: `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`
- [x] 2.2 Add worker configuration: `WORKER_POLL_INTERVAL`, `WORKER_MAX_RETRIES`, `WORKER_HEALTH_CHECK_INTERVAL`, `WORKER_PROCESSING_TIMEOUT`
- [x] 2.3 Add queue and webhook configuration: `QUEUE_BACKEND`, `ARBITER_WEBHOOK_URL`
- [x] 2.4 Add `SKIP_REVIEW` bypass configuration
- [x] 2.5 Update `.env.example` with all new environment variables

## 3. Task Queue

- [x] 3.1 Define abstract `TaskQueue` interface in `src/briefchain/arbiter/queue/base.py`
- [x] 3.2 Implement `DatabaseTaskQueue` in `src/briefchain/arbiter/queue/database.py` with `enqueue` and `dequeue`
- [x] 3.3 Create queue factory in `src/briefchain/arbiter/queue/factory.py` based on `QUEUE_BACKEND`
- [x] 3.4 Add unit tests for `DatabaseTaskQueue` in `tests/arbiter/test_queue.py`

## 4. Skill and LLM Integration

- [x] 4.1 Add `google-adk` dependency to `pyproject.toml`
- [x] 4.2 Implement skill loader in `src/briefchain/arbiter/skills/loader.py` using Google ADK to load `brief-review`
- [x] 4.3 Define Pydantic output schema in `src/briefchain/arbiter/skills/schemas.py` including a `thinking` field and `passed/score/issues/suggestions`
- [x] 4.4 Implement LLM client wrapper in `src/briefchain/arbiter/llm/client.py` using configured `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY`
- [x] 4.5 Add tests for skill loading and LLM client in `tests/arbiter/test_skills.py`

## 5. Worker

- [x] 5.1 Implement `ReviewHandler` in `src/briefchain/arbiter/handlers/review.py` to load skill, invoke LLM, and update review record
- [x] 5.2 Implement skip-review path in `ReviewHandler` to mark review as `force_skipped` when `SKIP_REVIEW=true`
- [x] 5.3 Implement `ArbiterWorker` main loop in `src/briefchain/arbiter/worker.py` with dequeue, dispatch, retry, and health recovery
- [x] 5.4 Implement webhook sender in `src/briefchain/arbiter/webhook.py` with post-transaction, fail-silent behavior
- [x] 5.5 Implement worker subprocess entrypoint in `src/briefchain/arbiter/__main__.py`
- [x] 5.6 Integrate worker spawn/terminate into `src/briefchain/api/main.py`
- [x] 5.7 Add worker tests in `tests/arbiter/test_worker.py`

## 6. API

- [x] 6.1 Create review request/response schemas in `src/briefchain/api/schemas/reviews.py`
- [x] 6.2 Implement `POST /api/v1/briefs/{brief_id}/reviews` in `src/briefchain/api/routes/reviews.py`
- [x] 6.3 Implement `GET /api/v1/briefs/{brief_id}/reviews/{review_id}` in `src/briefchain/api/routes/reviews.py`
- [x] 6.4 Modify `submit-review` action in `src/briefchain/api/routes/briefs.py` to trigger async review and return 202
- [x] 6.5 Update send/transfer action to reject send unless latest review is `passed`
- [x] 6.6 Add API tests in `tests/api/test_reviews.py`

## 7. Integration and Verification

- [x] 7.1 Run the full test suite and fix regressions
- [x] 7.2 Verify end-to-end review flow locally with SKIP_REVIEW fallback
- [x] 7.3 Update API documentation and `.env.example` if needed
