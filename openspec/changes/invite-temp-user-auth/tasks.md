## 1. Database Migration

- [x] 1.1 Create Alembic migration to add `brief_invites` table with columns `id`, `brief_id`, `nonce`, `token`, `name`, `temporary_user_id`, `from_user`, `final_user_id`, `accept_deadline`, `complete_deadline`, `invalidated_at`, `created_at`, `updated_at`
- [x] 1.2 Add unique indexes on `brief_invites.nonce` and `brief_invites.token`
- [x] 1.3 Add foreign keys from `brief_invites.brief_id`, `temporary_user_id`, `from_user`, and `final_user_id` to `users.id` / `briefs.brief_id`
- [x] 1.4 Drop the legacy `email_tokens` table and remove `EmailToken` model references
- [x] 1.5 Add `from_temporary_user_id` column to `users` table with foreign key to `users.id`

## 2. Data Models

- [x] 2.1 Create `src/briefchain/models/invite.py` with `BriefInvite` SQLAlchemy model
- [x] 2.2 Add `invites: Mapped[list[BriefInvite]]` relationship to `Brief` in `src/briefchain/models/brief.py`
- [x] 2.3 Remove `EmailToken` class from `src/briefchain/models/user.py`
- [x] 2.4 Export `BriefInvite` from `src/briefchain/models/__init__.py`
- [x] 2.5 Add `final_user_id` field to `BriefInvite` model
- [x] 2.6 Add `from_temporary_user_id` field to `User` model

## 3. Schemas

- [x] 3.1 Add optional `invite_token: str | None` field to `RegisterRequest` and `LoginRequest` in `src/briefchain/api/schemas/auth.py`
- [x] 3.2 Add `upgraded_from_temporary: bool = False` and `linked_temporary_user: UUID | None = None` fields to `AuthResponse`
- [x] 3.3 Create `src/briefchain/api/schemas/invites.py` with `InviteViewResponse`, `AcceptInviteRequest`, `RejectInviteRequest`, `BlockedInviteRequest`, `DoneInviteRequest`, and `InviteMetadataResponse`
- [x] 3.4 Update `SendBriefRequest` to add `is_temporary_user: bool` and make `recipient_email`/`recipient_phone` optional; update route/service to use the new parameter
- [x] 3.5 Extend `BriefLifecycleResponse` in `src/briefchain/api/schemas/briefs.py` to include optional `invite` metadata

## 4. Invite Service

- [x] 4.1 Create `src/briefchain/api/services/invites.py` with `generate_invite_token(brief_id, nonce, accept_deadline)` returning token string
- [x] 4.2 Implement `parse_invite_token(token)` that extracts `brief_id`, `nonce`, `accept_deadline_epoch`, and signature
- [x] 4.3 Implement `verify_invite_token_signature(token)` using HMAC-SHA256 over `brief_id_hex:nonce:accept_deadline_epoch` with `settings.jwt_secret_key`
- [x] 4.4 Implement `get_invite_by_token(session, token)` performing signature check → deadline check → nonce lookup → invalidated_at check
- [x] 4.5 Implement `create_invite(session, brief_id, from_user, recipient_name, recipient_email, recipient_phone, accept_deadline, complete_deadline, temporary_user_id)`
- [x] 4.6 Implement `invalidate_invites_for_temporary_user(session, temporary_user_id)` to set `invalidated_at=now()` on all valid invites for the user
- [x] 4.7 Implement `get_invite_by_brief_id(session, brief_id)` to find the active invite for a brief
- [x] 4.8 Update invite invalidation to also set `final_user_id`

## 5. Brief Service Changes

- [x] 5.1 Refactor `send_brief` to dispatch based on `is_temporary_user`: when false use existing `assigned_to` logic; when true use email/phone lookup
- [x] 5.2 Implement temporary-user lookup rules: registered user or temporary user with `final_user_id` → internal send; temporary user without `final_user_id` → reuse user_id and create new invite; not found → create new temporary user (allow empty email/phone) and create invite
- [x] 5.3 Ensure `send_brief` validates request fields based on `is_temporary_user`

## 6. Auth Service Changes

- [x] 6.1 Update `register_user` to migrate all briefs assigned to the temporary user whose `upstream_state` is not `done` / `cancelled` to the registered user
- [x] 6.2 Update `login_user` to reject `UserType.TEMPORARY` users with `TEMPORARY_USER_CANNOT_LOGIN`
- [x] 6.3 Update `login_user` to migrate all briefs assigned to the temporary user whose `upstream_state` is not `done` / `cancelled` to the logged-in user

## 7. Dependencies

- [x] 7.1 Add `get_invite_from_token(session, token)` to `src/briefchain/api/dependencies.py` that returns a loaded `BriefInvite`
- [x] 7.2 Define `InviteDep = Annotated[BriefInvite, Depends(get_invite_from_token)]`

## 8. Routes

- [x] 8.1 Create `src/briefchain/api/routes/invites.py` with `GET /invites/{token}`, `POST /invites/{token}/transfer?action=accept|reject`, and `POST /invites/{token}/downstream-actions?action=process|submit|open|delegate|block`
- [x] 8.2 Update `src/briefchain/api/routes/auth.py` to pass `invite_token` through to service functions
- [x] 8.3 Update `src/briefchain/api/routes/briefs.py` `send_brief` endpoint to accept the new external-recipient request schema
- [x] 8.4 Register the invites router in `src/briefchain/api/main.py` at `/api/v1`

## 9. Tests

- [x] 9.1 Add/update API tests for `is_temporary_user` send branches: anonymous, reuse existing temporary user, fallback to registered user, fallback to final_user_id
- [x] 9.2 Add/update API tests for auth with `invite_token` migrating all non-done/cancelled briefs
- [x] 9.3 Run `pytest tests/` and ensure all tests pass
- [x] 9.4 Run `ruff check src tests`
