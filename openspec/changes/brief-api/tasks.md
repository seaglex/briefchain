## 1. Project Setup

- [x] 1.1 Create `src/briefchain/api/services/briefs.py` service module
- [x] 1.2 Create `src/briefchain/api/schemas/briefs.py`, `transfers.py`, `feedbacks.py`, `chains.py`
- [x] 1.3 Create `src/briefchain/api/routes/briefs.py`, `brief_versions.py`, `brief_transfers.py`, `feedbacks.py`, `chains.py`
- [x] 1.4 Register new routers in `src/briefchain/api/main.py` under `/api/v1`

## 2. Shared Helpers

- [x] 2.1 Add brief ownership/permission helper in service layer (`require_creator`, `require_creator_or_assigned`, `require_participant`)
- [x] 2.2 Add brief response serialization helpers for list/detail/version modes
- [x] 2.3 Add cursor pagination helper for brief list and chain list

## 3. Brief Service Layer

- [x] 3.1 Implement `create_brief` service with root/child handling and initial version creation
- [x] 3.2 Implement `list_briefs` service with role/status filters and cursor pagination
- [x] 3.3 Implement `get_brief_detail` service returning latest version content
- [x] 3.4 Implement `get_brief_version` service returning a specific version content
- [x] 3.5 Implement `update_brief` service creating new version only when status is `draft`
- [x] 3.6 Implement lifecycle services (`submit`, `send`, `accept`, `reject`, `cancel`, `complete`) with state and permission checks

## 4. Brief Schemas

- [x] 4.1 Create brief list/response schema with list and detail modes
- [x] 4.2 Create brief create/update request schemas
- [x] 4.3 Create brief lifecycle response schema

## 5. Brief CRUD Routes (`/api/v1/briefs`)

- [x] 5.1 Implement `POST /briefs` to create root or child brief
- [x] 5.2 Implement `GET /briefs` with role/status filters and cursor pagination
- [x] 5.3 Implement `GET /briefs/:brief_id` returning the latest version content
- [x] 5.4 Implement `PATCH /briefs/:brief_id` to update draft brief and create new version

## 6. Brief Lifecycle Routes (`/api/v1/briefs/:brief_id/...`)

- [x] 6.1 Implement `POST /briefs/:brief_id/submit` (draft → reviewed)
- [x] 6.2 Implement `POST /briefs/:brief_id/send` (reviewed → sent, create transfer)
- [x] 6.3 Implement `POST /briefs/:brief_id/accept` (sent → accepted)
- [x] 6.4 Implement `POST /briefs/:brief_id/reject` (sent → draft)
- [x] 6.5 Implement `POST /briefs/:brief_id/cancel` (non-done → cancelled)
- [x] 6.6 Implement `POST /briefs/:brief_id/complete` (accepted → done)

## 7. Brief Versions Routes

- [x] 7.1 Implement `GET /briefs/:brief_id/versions` listing all versions
- [x] 7.2 Implement `GET /briefs/:brief_id/versions/:version` returning a specific version content

## 8. Brief Transfers Routes

- [x] 8.1 Implement `GET /briefs/:brief_id/transfers`

## 9. Feedback Routes

- [x] 9.1 Create feedback request/response schemas
- [x] 9.2 Implement `POST /briefs/:brief_id/feedbacks`
- [x] 9.3 Implement `GET /briefs/:brief_id/feedbacks`
- [x] 9.4 Implement `GET /feedbacks/:feedback_id`

## 10. Chain Routes

- [x] 10.1 Create chain response schema with tree structure
- [x] 10.2 Implement `GET /chains`
- [x] 10.3 Implement `GET /chains/:chain_id`

## 11. Testing

- [x] 11.1 Add pytest fixtures for brief, transfer, feedback, and chain test data
- [x] 11.2 Write tests for brief CRUD success and validation errors
- [x] 11.3 Write tests for brief lifecycle state transitions and permissions
- [x] 11.4 Write tests for brief versions list and specific version detail
- [x] 11.5 Write tests for brief transfers
- [x] 11.6 Write tests for feedback creation and retrieval
- [x] 11.7 Write tests for chain list and detail with tree structure

## 12. Quality & Verification

- [x] 12.1 Run `ruff check` and `ruff format` on `src/briefchain/api/` and `tests/`
- [x] 12.2 Verify all imports resolve with `python -c "from briefchain.api.main import app"`
- [x] 12.3 Run full test suite and ensure all tests pass
