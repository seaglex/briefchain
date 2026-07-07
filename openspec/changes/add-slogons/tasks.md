## 1. Shared Slogan Component

- [x] 1.1 Create `web/components/ProductSlogans.tsx` with the three slogans, titles, and short descriptions.
- [x] 1.2 Add basic styling for the slogan cards to match the existing design system.
- [x] 1.3 Decide and implement icons for each slogan (Lucide, CSS shapes, or emoji fallback).

## 2. Landing Page

- [x] 2.1 Create `web/app/landing/page.tsx` as an independent page (without `AppShell` auth requirement).
- [x] 2.2 Render `ProductSlogans` on the landing page with a hero title and a "进入应用" button.
- [x] 2.3 Ensure the landing page is publicly accessible without authentication.

## 3. Auth Pages

- [x] 3.1 Add `ProductSlogans` below the login form in `web/app/login/page.tsx`.
- [x] 3.2 Add `ProductSlogans` below the register form in `web/app/register/page.tsx`.
- [x] 3.3 Verify layout does not break on narrow screens.

## 4. Invite Page

- [x] 4.1 Add `ProductSlogans` below the invite content/actions in `web/app/invites/[token]/page.tsx`.
- [x] 4.2 Ensure slogans render correctly in both loading and loaded states.

## 5. Brand Link

- [x] 5.1 Locate the BriefChain brand link in `AppShell` and/or `Sidebar`.
- [x] 5.2 Change the brand link target from `/` to `/landing`.
- [x] 5.3 Verify the link works for both logged-in and logged-out users.

## 6. Verification

- [x] 6.1 Run `npx tsc --noEmit` and fix any type errors.
- [x] 6.2 Visually verify login, register, invite, and landing pages render slogans correctly.
- [x] 6.3 Verify clicking the top-left BriefChain brand navigates to `/landing`.
