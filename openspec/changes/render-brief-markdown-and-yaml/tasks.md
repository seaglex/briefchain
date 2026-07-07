## 1. Setup

- [x] 1.1 Install `marked` in the web workspace.
- [x] 1.2 Add `@types/marked` if needed for TypeScript support.

## 2. YAML Metadata Formatter

- [x] 2.1 Create `web/components/BriefYamlMetadata.tsx` to format `title`, `priority`, `estimated_man_days`, `expected_completion_at` as YAML.
- [x] 2.2 Handle null/undefined values gracefully.

## 3. Markdown Content Renderer

- [x] 3.1 Create `web/components/MarkdownRenderer.tsx` that accepts a markdown string and returns rendered HTML using `marked`.
- [x] 3.2 Disable raw HTML rendering to avoid XSS.
- [x] 3.3 Add scoped CSS for rendered Markdown elements.

## 4. Brief Detail Integration

- [x] 4.1 Update `web/components/BriefDetail.tsx` to render YAML metadata at the top of the content card.
- [x] 4.2 Update `web/components/BriefDetail.tsx` to render `brief.content` via `MarkdownRenderer` instead of plain text.
- [x] 4.3 Ensure the component remains compatible with draft version viewing.

## 5. Verification

- [x] 5.1 Run `npx tsc --noEmit` and fix any type errors.
- [x] 5.2 Manually verify a brief with Markdown content renders correctly.
- [x] 5.3 Verify YAML metadata displays all four fields and omits missing values cleanly.
