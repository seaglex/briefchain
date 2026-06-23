## 1. API Client and Types

- [x] 1.1 Add TypeScript types for temporary-user send request (`is_temporary_user`, `recipient_name`, `recipient_email`, `recipient_phone`) and invite response (`invite.invite_url`, `accept_deadline`, `complete_deadline`).
- [x] 1.2 Add `apiFetch` helper calls for `GET /invites/{token}`, `POST /invites/{token}/accept`, `POST /invites/{token}/reject`, `POST /invites/{token}/blocked`, and `POST /invites/{token}/done`.

## 2. Brief Detail Send Dialog

- [x] 2.1 Update the send dialog on the Brief detail page to show a choice between "Registered user" and "Temporary user".
- [x] 2.2 Add the temporary user form fields: recipient name (required) and email or phone (optional).
- [x] 2.3 Call `POST /api/v1/briefs/{brief_id}/send` with `is_temporary_user=true` when the temporary user form is submitted.
- [x] 2.4 Display the returned invite link with a copy-to-clipboard button and a success indicator.

## 3. Public Invite Page Layout

- [x] 3.1 Create the Next.js route `web/app/invites/[token]/page.tsx`.
- [x] 3.2 Build the standalone header component with BriefChain icon/name, tagline, recipient welcome message, and login/register links (no left sidebar).
- [x] 3.3 Add client-side data fetching for `GET /invites/{token}` and handle loading / error states.

## 4. Invite Page Brief Detail Integration

- [x] 4.1 Reuse the existing Brief detail component to render the Brief returned by the invite endpoint.
- [x] 4.2 Pass a flag to hide creator-only actions (send, edit, submit) when rendered in invite view mode.
- [x] 4.3 Render invite-specific action controls (accept, reject, block, complete) below the Brief detail.

## 5. Error and Edge Case Handling

- [x] 5.1 Show "Invite expired" error with a login link when the API returns `INVITE_EXPIRED`.
- [x] 5.2 Show "Invite invalidated" error with a login link when the API returns `INVITE_INVALIDATED`.
- [x] 5.3 Handle generic token errors (invalid format, network failure) with a user-friendly message.

## 6. Verification

- [x] 6.1 Manually test sending a Brief to a temporary user and copying the invite link.
- [x] 6.2 Open the invite link in an incognito window and verify the header, Brief detail, and error states.
- [x] 6.3 Confirm existing Brief detail page behavior for registered users remains unchanged.
