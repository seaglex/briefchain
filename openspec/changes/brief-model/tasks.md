## 1. Project Setup

- [x] 1.1 Verify Python 3.13+ and `uv` availability
- [x] 1.2 Ensure SQLAlchemy 2.0+ and Alembic are listed as dependencies
- [x] 1.3 Create `src/briefchain/models/` package with `__init__.py`

## 2. Base Models

- [x] 2.1 Create `src/briefchain/models/base.py` with `DeclarativeBase`
- [x] 2.2 Implement `UUIDPrimaryKeyMixin` with `Mapped[uuid.UUID]` primary key
- [x] 2.3 Implement `TimestampMixin` with `created_at` and `updated_at` columns

## 3. Enumerations

- [x] 3.1 Create `src/briefchain/models/enums.py`
- [x] 3.2 Define `BriefStatus` enum with all 7 status values
- [x] 3.3 Define `BriefPriority` enum with p0/p1/p2/p3 values
- [x] 3.4 Define `FeedbackType` enum with blocked/progress/completion values
- [x] 3.5 Define `ArbiterReviewStatus` enum with passed/failed/force_skipped values

## 4. Brief Models

- [x] 4.1 Implement `Brief` model in `src/briefchain/models/brief.py`
- [x] 4.2 Implement self-referential `parent` / `children` relationships on `Brief`
- [x] 4.3 Implement `BriefVersion` model with composite primary key `(brief_id, version)`
- [x] 4.4 Implement `BriefTransferHistory` model mapped to `brief_transfer_history` with sent/accepted/rejected timestamps
- [x] 4.5 Implement `BriefChain` model with `chain_id` as primary key
- [x] 4.6 Implement `BriefArbiterReview` model with JSON `issues` and `suggestions`
- [x] 4.7 Wire `Brief` relationships to versions, transfers, chain, and reviews
- [x] 4.8 Add `lazy="raise"` to all `Brief` and related model relationships

## 5. Feedback Models

- [x] 5.1 Implement `Feedback` model in `src/briefchain/models/feedback.py`
- [x] 5.2 Implement `FeedbackArbiterReview` model with JSON `result`
- [x] 5.3 Wire `Feedback` and `Brief` relationships
- [x] 5.4 Add `lazy="raise"` to all `Feedback` relationships

## 6. Alembic Migration

- [x] 6.1 Run `alembic init alembic` and configure `env.py` to import models
- [x] 6.2 Configure `alembic.ini` to read `sqlalchemy.url` from environment variable
- [x] 6.3 Generate initial revision with `alembic revision --autogenerate -m "init brief models"`
- [x] 6.4 Verify migration can upgrade and downgrade against SQLite file

## 7. SQLite Unit Tests

- [x] 7.1 Add pytest + pytest-asyncio dependencies if not present
- [x] 7.2 Create `tests/conftest.py` with SQLite `:memory:` engine and session fixture
- [x] 7.3 Write test inserting 1 root brief and 2 child briefs
- [x] 7.4 Write test querying chain list by `root_id` and assert 3 briefs returned
- [x] 7.5 Run test suite and ensure all tests pass

## 8. Quality & Verification

- [x] 8.1 Run `ruff check` and `ruff format` on `src/briefchain/models/` and `tests/`
- [x] 8.2 Add type annotations to all model fields and relationships
- [x] 8.3 Add Google-style docstrings to all modules, classes, and enums
- [x] 8.4 Verify all imports resolve with `python -c "from briefchain.models import *"`
