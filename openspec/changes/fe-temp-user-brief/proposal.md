## Why

The backend already supports sending Briefs to external (temporary) users via signed invite links. Creators currently cannot generate these links from the frontend. This change adds the UI to send Briefs to temporary users and a public invite page where recipients can view the Brief and take action.

## What Changes

- On the creator Brief detail page, extend the "Send to downstream" flow with an option to send to a temporary user.
- Add a form for recipient name and email or phone (optional) when sending to a temporary user.
- Display the generated invite link with a copy-to-clipboard action after sending.
- Create a new public page at `/invites/{token}` that:
  - Shows a top header with the BriefChain brand, tagline, and login/register links for the recipient.
  - Reuses the existing Brief detail component to render the Brief.
- Update frontend API helpers and types for the invite endpoints.

## Capabilities

### New Capabilities

- `send-temp-user-invite`: Dialog / form on the creator Brief detail page for sending a Brief to an external temporary user and copying the invite link.
- `invite-view-page`: Public page for invite recipients to view the Brief, accept, reject, block, or complete it via token-based endpoints.

### Modified Capabilities

- None

## Impact

- Frontend (`web/`): new route `/invites/[token]`, updates to Brief detail send UI, API client additions.
- Backend (`src/briefchain/api/`): no new backend endpoints; reuses existing `/api/v1/briefs/{id}/send` and `/invites/{token}*` endpoints.
- Design docs: references `docs/mvp_design/05-invite-link-design.md`.
