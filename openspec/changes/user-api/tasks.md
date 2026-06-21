## 1. Project Setup

- [x] 1.1 Add FastAPI, python-jose, passlib, and bcrypt dependencies to `pyproject.toml`
- [x] 1.2 Create `src/briefchain/api/` package structure (`main.py`, `dependencies.py`, `routes/`, `schemas/`)
- [x] 1.3 Add JWT secret configuration via environment variable with local fallback

## 2. Shared Components

- [x] 2.1 Implement `get_db_session` dependency
- [x] 2.2 Implement `get_current_user` dependency using JWT Bearer token
- [x] 2.3 Implement password hashing helper with passlib bcrypt
- [x] 2.4 Implement JWT encode/decode helpers
- [x] 2.5 Implement unified API error response model and exception handler

## 3. Pydantic Schemas

- [x] 3.1 Create `src/briefchain/api/schemas/auth.py` with register/login requests and auth response
- [x] 3.2 Create `src/briefchain/api/schemas/users.py` with user list/detail responses and masking logic
- [~] 3.3 Token schemas are intentionally omitted — `/tokens` endpoints are not implemented in this change

## 4. Auth Routes (`/api/v1/auth`)

- [x] 4.1 Implement `POST /auth/register` with email/phone validation and duplicate checks
- [x] 4.2 Implement `POST /auth/login` with email/phone auto-detection and password verification
- [x] 4.3 Implement `GET /auth/me` returning current user profile
- [x] 4.4 Implement `POST /auth/logout` returning 204 No Content

## 5. User Routes (`/api/v1/users`)

- [x] 5.1 Implement `GET /users` returning paginated user list with masked sensitive fields
- [x] 5.2 Implement `GET /users/:user_id` returning user profile with viewer-aware masking

## 6. Application Wiring

- [x] 6.1 Create FastAPI app in `src/briefchain/api/main.py`
- [x] 6.2 Register auth and users routers with `/api/v1` prefix
- [x] 6.3 Add health check or root endpoint

## 7. Testing

- [x] 7.1 Add pytest fixtures for FastAPI `TestClient`, database session, and JWT secret
- [x] 7.2 Write tests for register/login success and validation errors
- [x] 7.3 Write tests for current user and unauthorized access
- [x] 7.4 Write tests for user list/detail with sensitive field masking

## 8. Quality & Verification

- [x] 8.1 Run `ruff check` and `ruff format` on `src/briefchain/api/` and `tests/`
- [x] 8.2 Verify all imports resolve with `python -c "from briefchain.api.main import app"`
- [x] 8.3 Run full test suite and ensure all tests pass

## 9. Service Layer Refactor

- [x] 9.1 Create `src/briefchain/api/services/users.py` to host user domain service functions
- [x] 9.2 Implement `register_user(session, request) -> AuthResponse` in the service layer
- [x] 9.3 Implement `login_user(session, request) -> AuthResponse` in the service layer
- [x] 9.4 Implement `get_current_user_profile(current_user) -> UserResponse` in the service layer
- [x] 9.5 Implement `list_users(session, viewer_user_id, page, page_size) -> UserListResponse` in the service layer
- [x] 9.6 Implement `get_user_by_id(session, user_id, viewer_user_id) -> UserResponse` in the service layer
- [x] 9.7 Refactor `src/briefchain/api/routes/auth.py` so each endpoint only parses input, calls the service, and returns the response
- [x] 9.8 Refactor `src/briefchain/api/routes/users.py` so each endpoint only parses input, calls the service, and returns the response
- [x] 9.9 Run `ruff check`, `ruff format`, and the full test suite after the refactor
