## ADDED Requirements

### Requirement: Login page renders and accepts credentials
The system SHALL provide a Next.js login page at `/login` that matches the visual style of the BriefChain static prototype.

#### Scenario: Login page loads
- **WHEN** an unauthenticated user navigates to `/login`
- **THEN** the page displays the BriefChain logo, an email/phone input, a password input, a primary "登录" button, and a link to the registration page

#### Scenario: Login form validates empty fields
- **WHEN** the user clicks the login button without entering email/phone or password
- **THEN** the page displays a validation error and does not submit the form

### Requirement: Login page authenticates via Next.js API Route
The system SHALL call the internal Next.js API Route `POST /api/auth/login`, which proxies to the backend and sets an `httpOnly` session cookie.

#### Scenario: Successful login
- **WHEN** the user enters valid credentials and clicks the login button
- **THEN** the system calls `POST /api/auth/login`, the API Route forwards `{ email_or_phone, password }` to backend `POST /auth/login`, sets the returned JWT in an `httpOnly` cookie, and redirects the user to the main application page `/`

#### Scenario: Failed login
- **WHEN** the user enters invalid credentials and clicks the login button
- **THEN** the system calls `POST /api/auth/login`, the API Route returns the backend error message, and the page displays the error without setting a session cookie

### Requirement: Registration page renders and accepts account details
The system SHALL provide a Next.js registration page at `/register` that matches the visual style of the BriefChain static prototype.

#### Scenario: Registration page loads
- **WHEN** an unauthenticated user navigates to `/register`
- **THEN** the page displays the BriefChain logo, name input, email input, phone input, password input, a primary "注册" button, and a link to the login page

#### Scenario: Registration form validates required fields
- **WHEN** the user clicks the registration button without entering name, password, or at least one of email/phone
- **THEN** the page displays a validation error and does not submit the form

#### Scenario: Registration form validates email format
- **WHEN** the user enters an email that is not a valid email address
- **THEN** the page displays a validation error and does not submit the form

### Requirement: Registration page creates account via Next.js API Route
The system SHALL call the internal Next.js API Route `POST /api/auth/register`, which proxies to the backend and sets an `httpOnly` session cookie.

#### Scenario: Successful registration
- **WHEN** the user enters valid registration details and clicks the registration button
- **THEN** the system calls `POST /api/auth/register`, the API Route forwards `{ name, email?, phone?, password }` to backend `POST /auth/register`, sets the returned JWT in an `httpOnly` cookie, and redirects the user to the main application page `/`

#### Scenario: Failed registration
- **WHEN** the user enters details that conflict with an existing account or fail backend validation
- **THEN** the system calls `POST /api/auth/register`, the API Route returns the backend error message, and the page displays the error without setting a session cookie

### Requirement: Session is persisted in an httpOnly cookie and guarded by middleware
The system SHALL store the JWT in an `httpOnly` cookie after successful login or registration and use Next.js Middleware to guard application routes.

#### Scenario: Session cookie persistence
- **WHEN** a user successfully logs in or registers
- **THEN** the system stores the JWT in an `httpOnly`, `Secure`, `SameSite=Lax` cookie that is inaccessible to client-side JavaScript

#### Scenario: Authenticated users bypass auth pages
- **WHEN** an authenticated user navigates to `/login` or `/register`
- **THEN** Next.js Middleware redirects the user to `/`

#### Scenario: Unauthenticated users cannot access main application
- **WHEN** an unauthenticated user navigates to `/` or any other protected route
- **THEN** Next.js Middleware redirects the user to `/login`

### Requirement: Logout clears session
The system SHALL provide a logout action that clears the `httpOnly` cookie and returns the user to the login page.

#### Scenario: User logs out
- **WHEN** the user triggers logout from the main application
- **THEN** the system calls `POST /api/auth/logout`, the API Route forwards to backend `POST /auth/logout`, clears the session cookie, and redirects the user to `/login`

### Requirement: Frontend project lives in the `web/` directory
The system SHALL place all Next.js frontend code, including pages, API routes, middleware, styles, and components, under the `web/` directory.

#### Scenario: Project structure
- **WHEN** a developer opens the repository
- **THEN** the Next.js application entry point, `package.json`, `app/`, `middleware.ts`, and related configuration files are located under `web/`
