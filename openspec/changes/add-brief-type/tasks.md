## 1. Backend Models and Enums

- [x] 1.1 Add `BriefType` StrEnum to `src/briefchain/models/enums.py` with values `idea`, `epic`, `feature`, `story`.
- [x] 1.2 Add `type: Mapped[BriefType]` column to `Brief` model in `src/briefchain/models/brief.py` with `nullable=False, default=BriefType.IDEA`.
- [x] 1.3 Add `type: Mapped[BriefType]` column to `BriefVersion` model in `src/briefchain/models/brief.py` with `nullable=False, default=BriefType.IDEA`.

## 2. API Schema Updates

- [x] 2.1 Add `BriefType` enum to `src/briefchain/api/schemas/briefs.py` and import it.
- [x] 2.2 Add `type: BriefType` field to `BriefListItem` response schema.
- [x] 2.3 Add `type: BriefType` field to `BriefDetail` response schema.
- [x] 2.4 Add `type: BriefType = BriefType.IDEA` field to `BriefCreateRequest`.
- [x] 2.5 Add `type: BriefType | None = None` field to `BriefPatchRequest`.
- [x] 2.6 Add `type: BriefType | None = None` field to `BriefUpdateActionRequest`.

## 3. Service Layer Updates

- [x] 3.1 Update brief creation logic in `src/briefchain/api/services/briefs.py` to persist `type` on `Brief` and initial `BriefVersion`.
- [x] 3.2 Update draft patch logic to apply `type` changes to the current draft `BriefVersion` and sync to `Brief` when finalized.
- [x] 3.3 Update upstream update action logic to accept and persist `type` changes.
- [x] 3.4 Ensure `BriefDetail` and list responses include the `type` field.

## 4. Database Migration

- [x] 4.1 Generate Alembic migration to add `type` column to `briefs` and `brief_versions` tables with default `idea` and `nullable=False`.
- [x] 4.2 Review generated migration and run it against the local database.
- [x] 4.3 Verify existing briefs are backfilled with `idea` type.

## 5. Frontend Types

- [x] 5.1 Add `BriefType` union type (`'idea' | 'epic' | 'feature' | 'story'`) to the shared brief type definitions in `web/components/BriefDetail.tsx` or a shared types file.
- [x] 5.2 Add `type` field to the brief detail/list TypeScript interfaces.

## 6. Frontend Detail Page Header

- [x] 6.1 Update `web/app/briefs/[brief_id]/page.tsx` to render the brief type before the header title in `Type - Brief 详情` format.
- [x] 6.2 Add a label map for display names (`idea` → `Idea`, etc.).
- [x] 6.3 Handle draft version header so type label reflects the viewed version's type when applicable.

## 7. Frontend Create/Edit Forms

- [x] 7.1 Add a type selector to `web/components/NewBriefForm.tsx` with options `idea / epic / feature / story` and default `idea`.
- [x] 7.2 Add a type selector to the brief editing form in `web/components/BriefActions.tsx` (or the form it renders) so draft type can be changed.
- [x] 7.3 Ensure the selected type is included in create/patch/update API requests.

## 8. Verification

- [x] 8.1 Run backend tests (if present) and verify no regressions.
- [x] 8.2 Manually verify creating a brief with each type, editing type, and viewing the detail header.
- [x] 8.3 Verify existing briefs without an explicit type render as `Idea - Brief 详情`.
