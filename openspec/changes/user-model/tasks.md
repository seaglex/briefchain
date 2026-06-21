## 1. Enumerations

- [x] 1.1 Add `UserType` enum with registered/oauth/external/temporary values

## 2. User Models

- [x] 2.1 Create `src/briefchain/models/user.py`
- [x] 2.2 Implement `User` model with user type fields
- [x] 2.3 Implement `UserIdentity` model with provider unique constraint
- [x] 2.4 Implement `EmailToken` model
- [x] 2.5 Wire `User` relationships to identities
- [x] 2.6 Add `lazy="raise"` to all `User` relationships

## 3. Model Exports

- [x] 3.1 Update `src/briefchain/models/__init__.py` to export user models and enums
- [x] 3.2 Update `alembic/env.py` to import user models for autogenerate

## 4. Alembic Migration

- [x] 4.1 Generate new revision with `alembic revision --autogenerate -m "add user models"`
- [x] 4.2 Verify migration can upgrade and downgrade against SQLite file

## 5. SQLite Unit Tests

- [x] 5.1 Write test creating registered, oauth, external, and temporary users
- [x] 5.2 Write test binding multiple identities to one user
- [x] 5.3 Write test creating and using an email token
- [x] 5.4 Run test suite and ensure all tests pass

## 6. Quality & Verification

- [x] 6.1 Run `ruff check` and `ruff format` on `src/briefchain/models/` and `tests/`
- [x] 6.2 Add type annotations to all model fields and relationships
- [x] 6.3 Add Google-style docstrings to all modules, classes, and enums
- [x] 6.4 Verify all imports resolve with `python -c "from briefchain.models import *"`
