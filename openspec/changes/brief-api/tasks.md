## 1. Project Setup

- [x] 1.1 Create `src/briefchain/api/services/briefs.py` service module
- [x] 1.2 Create `src/briefchain/api/schemas/briefs.py`, `transfers.py`, `feedbacks.py`, `chains.py`
- [x] 1.3 Create `src/briefchain/api/routes/briefs.py`, `brief_transfers.py`, `brief_actions.py`, `brief_versions.py`, `feedbacks.py`, `chains.py`
- [x] 1.4 Register new routers in `src/briefchain/api/main.py` under `/api/v1`

## 2. Shared Helpers

- [x] 2.1 Add brief ownership/permission helper in service layer (`require_creator`, `require_creator_or_assigned`, `require_participant`, `require_assigned`)
- [x] 2.2 Add brief response serialization helpers for list/detail/version/tree modes with `*_id` / `*_name` flat user fields
- [x] 2.3 Add cursor pagination helper for brief list, feedback list, and chain list

## 3. Brief Service Layer

- [x] 3.1 Implement `create_brief` service with root/child handling, initial draft version creation, and `current_version` null
- [x] 3.2 Implement `list_briefs` service with role / upstream_state / downstream_state / root_id filters and cursor pagination
- [x] 3.3 Implement `get_brief_detail` service returning requested version content, `is_current`, and `unsent_version`
- [x] 3.4 Implement `list_brief_versions` service returning version status and modifier name snapshots
- [x] 3.5 Implement `patch_brief` service modifying draft/reviewed version in place or creating a new draft version when the current version status is `sent`
- [x] 3.6 Implement `review_brief` service transitioning current draft version status to "reviewed"
- [x] 3.7 Implement transfer services (`send`, `accept`, `reject`) with temporary-user support and name snapshots
- [x] 3.8 Implement upstream-action services (`cancel`, `suspend`, `resume`, `approve`, `reject_submit`, `update`) with feedback creation
- [x] 3.9 Implement downstream-action services (`process`, `submit`, `open`, `delegate`, `block`) with feedback creation

## 4. Brief Schemas

- [x] 4.1 Create brief list/response schema with list and detail modes and flat user fields
- [x] 4.2 Create brief create / patch / review / update request schemas
- [x] 4.3 Create brief lifecycle response schema
- [x] 4.4 Create brief version response schema including `status`

## 5. Brief CRUD Routes (`/api/v1/briefs`)

- [x] 5.1 Implement `POST /briefs` to create root or child brief
- [x] 5.2 Implement `GET /briefs` with role / upstream_state / downstream_state / root_id filters and cursor pagination
- [x] 5.3 Implement `GET /briefs/:brief_id?version=` returning the requested version content
- [x] 5.4 Implement `POST /briefs/:brief_id/editing?action=patch` to update draft brief content
- [x] 5.5 Implement `POST /briefs/:brief_id/editing?action=submit-review` to submit current version for review

## 6. Brief Transfer Routes (`/api/v1/briefs/:brief_id/transfer`)

- [x] 6.1 Implement `POST /briefs/:brief_id/transfer?action=send` (reviewed or sent → sent, create transfer, support temporary user, allow re-sending after rejection)
- [x] 6.2 Implement `POST /briefs/:brief_id/transfer?action=accept` (sent → in_process, opened)
- [x] 6.3 Implement `POST /briefs/:brief_id/transfer?action=reject` (sent → editing)

## 7. Brief Upstream-action Routes (`/api/v1/briefs/:brief_id/upstream-actions`)

- [x] 7.1 Implement `POST ...?action=cancel` (→ cancelled, preserve downstream_state)
- [x] 7.2 Implement `POST ...?action=suspend` (→ suspended, preserve downstream_state)
- [x] 7.3 Implement `POST ...?action=resume` (suspended → in_process)
- [x] 7.4 Implement `POST ...?action=approve` (in_process + submitted → done)
- [x] 7.5 Implement `POST ...?action=reject_submit` (submitted → opened)
- [x] 7.6 Implement `POST ...?action=update` (new version sent, downstream_state → opened)

## 8. Brief Downstream-action Routes (`/api/v1/briefs/:brief_id/downstream-actions`)

- [x] 8.1 Implement `POST ...?action=process` (progress feedback, no state change)
- [x] 8.2 Implement `POST ...?action=submit` (→ submitted)
- [x] 8.3 Implement `POST ...?action=open` (→ opened)
- [x] 8.4 Implement `POST ...?action=delegate` (→ delegated)
- [x] 8.5 Implement `POST ...?action=block` (→ blocked)

## 9. Brief Versions Routes

- [x] 9.1 Implement `GET /briefs/:brief_id/versions` listing all versions with `status`

## 10. Brief Transfers Routes

- [x] 10.1 Implement `GET /briefs/:brief_id/transfers` with `from_user_name` / `to_user_name` snapshots

## 11. Feedback Routes

- [x] 11.1 Create feedback request/response schemas with `is_to_down` and direction-aware type
- [x] 11.2 Implement `GET /briefs/:brief_id/feedbacks` with `type` / `is_to_down` filters
- [x] 11.3 Implement `GET /feedbacks/:feedback_id` detail with full content and attachments

## 12. Chain Routes

- [x] 12.1 Create chain response schema with `owner_id`, `owner_name`, `priority`, and tree structure
- [x] 12.2 Implement `GET /chains`
- [x] 12.3 Implement `GET /chains/:chain_id`

## 13. Testing

- [x] 13.1 Add pytest fixtures for brief, transfer, feedback, and chain test data using new dual-state fields
- [x] 13.2 Write tests for brief CRUD success and validation errors
- [x] 13.3 Write tests for editing patch/review behavior
- [x] 13.4 Write tests for brief transfer state transitions and permissions
- [x] 13.5 Write tests for upstream-actions and downstream-actions state transitions and permissions
- [x] 13.6 Write tests for brief versions list
- [x] 13.7 Write tests for brief transfers list
- [x] 13.8 Write tests for feedback listing and detail
- [x] 13.9 Write tests for chain list and detail with tree structure

## 14. Quality & Verification

- [x] 14.1 Run `ruff check` and `ruff format` on `src/briefchain/api/` and `tests/`
- [x] 14.2 Verify all imports resolve with `python -c "from briefchain.api.main import app"`
- [x] 14.3 Run full test suite and ensure all tests pass
