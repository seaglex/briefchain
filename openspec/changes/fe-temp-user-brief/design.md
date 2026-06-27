## Context

The backend already supports sending Briefs to external recipients through temporary users and signed invite tokens (`docs/mvp_design/05-invite-link-design.md`). The API endpoint has moved into the new transfer group:

- `POST /api/v1/briefs/{brief_id}/transfer?action=send` with `is_temporary_user=true` returns an invite URL.
- `GET /invites/{token}` and related action endpoints are public and token-secured.

This change is purely frontend: expose the temporary-user send flow to creators and build the public invite recipient page.

## Goals / Non-Goals

**Goals:**
- In the creator Brief detail page, allow choosing "Send to temporary user" when sending downstream.
- Collect recipient name and optional one of the email or phone for the temporary user.
- Display the invite link returned by the backend and let the creator copy it.
- Build a public page at `/invites/{token}` with a dedicated header (no left sidebar) that reuses the existing Brief detail view.
- Link login and registration flows from the invite page header.

**Non-Goals:**
- Changing backend API behavior or data models.
- Implementing temporary-user registration / login upgrade flows (the links are present; the flows themselves are handled separately).
- Email or SMS delivery (the link is copied and shared manually).

## Decisions

1. **Reuse the existing Brief detail component on the invite page**
   - The backend `GET /invites/{token}` returns a `brief` object with the same shape as `GET /api/v1/briefs/{brief_id}`.
   - Reusing the component keeps behavior consistent and avoids duplicate presentation logic.

2. **Single `email_or_phone` input field on the send form**
   - The user request asks for "email_or_phone". Using one field keeps the UI minimal.
   - Frontend sends the value as `recipient_email`; if it looks like a phone number it can be sent as `recipient_phone`.
   - This matches the backend schema which accepts either field as optional.

3. **Invite page is a standalone layout without the application sidebar**
   - Public recipients should not see the creator navigation sidebar.
   - The page uses its own top header with brand, tagline, and login/register links.

4. **Copy-to-clipboard uses the browser Clipboard API**
   - Modern, no extra dependency.
   - Fallback to selecting the URL text for manual copy if permission is denied.

5. **Token validation errors are surfaced on the invite page**
   - Expired, invalid, or invalidated tokens show an error message and a link to login.
   - No automatic redirect; the error explains what happened.

6. **Invite page actions align with the new brief lifecycle**
   - Accept/reject belong to the transfer phase and use token-based invite endpoints.
   - After accepting, the recipient can perform downstream actions (submit / block / open / delegate) through token-based invite endpoints that map to the new downstream-actions logic.
   - Creator-only actions (edit, review, send, cancel, suspend, resume, approve, reject_submit, update) are hidden on the invite page.

## Risks / Trade-offs

- **[Risk] Invite page briefly shows layout shift while fetching.**
  - *Mitigation*: Use a loading state and suspend Brief detail rendering until data arrives.

- **[Risk] Reusing the Brief detail component may expose creator-only actions to temporary users.**
  - *Mitigation*: The public page passes an `isInviteView` or `readOnly` flag to hide send/edit/review/submit actions. Action buttons (accept/reject/submit/block/open/delegate) are rendered separately by the invite page itself.

- **[Trade-off] Email-or-phone single field is less explicit than two separate fields.**
  - Keeps the form short and matches the user's wording. If validation becomes complex later, it can be split into two fields.
