# 07 — Authentication Requirements

## 1. Purpose

This document defines the requirements for adding a simple authentication layer to the existing ZAP Security POC web application.

The authentication functionality is an additional layer on top of the existing application. The existing ZAP assessment workflow, findings, reports, and assessment functionality must remain unchanged unless explicitly required for authentication integration.

This document takes precedence over any authentication-related assumptions in the original project documentation. All other requirements from the original project documentation remain unchanged.

---

## 2. Authentication Scope

The application will provide a simple authentication layer consisting of:

- User account signup
- User login
- User logout
- Protection of the assessment application from unauthenticated access
- Persistent user accounts stored in the local SQLite database

The authentication implementation should use Django's built-in authentication framework.

No third-party authentication framework is required.

---

## 3. Out of Scope

The following functionality is explicitly out of scope:

- Authorization
- User roles
- Permissions beyond basic authentication
- Admin/user role management
- User-to-assessment mapping
- Assessment history per user
- User-specific ZAP scan ownership
- Multi-user/concurrent assessment management
- OAuth
- Google/Microsoft/social login
- JWT authentication
- MFA/2FA
- Email verification
- Email-based password reset
- CAPTCHA
- MySQL or other external database
- Custom authentication framework
- Custom password hashing
- Persistent assessment state

The existing single-user assessment model remains unchanged.

---

## 4. User Model

Use Django's built-in user authentication model unless a technical limitation requires otherwise.

Do not create a custom user table for this POC.

The application should support creation of multiple user accounts.

All authenticated users have the same application capabilities because authorization and role management are out of scope.

Conceptually:

    User A ──┐
    User B ──┤
    User C ──┼──> Same Application / Assessment Dashboard
    User D ──┘

There must be no relationship between a Django user account and an assessment instance.

---

## 5. Password Requirements

User passwords must be handled using Django's built-in password management functionality.

Passwords must never be stored in plaintext.

The application must rely on Django's password hashing and validation mechanisms.

The application should not implement custom password hashing or encryption.

The database should contain Django-managed password hashes rather than the user's original password.

---

## 6. Database Requirements

Use the existing local SQLite database.

No external database server is required.

The existing:

    db.sqlite3

database should be used for persistent authentication data.

User accounts must remain available after the Django application is stopped and restarted.

Example:

    User signs up
        ↓
    Account stored in SQLite
        ↓
    Django application stopped
        ↓
    Django application restarted
        ↓
    User can log in using the existing account

Assessment state does not need to survive an application restart.

Authentication persistence and assessment persistence are separate concerns.

---

## 7. Signup Requirements

Provide a simple signup page.

The signup form should contain the minimum information required for account creation.

Required fields:

- Username
- Password
- Password confirmation

Email is optional and should not be required for this POC.

The signup process should:

1. Validate the submitted information.
2. Reject an already-existing username.
3. Validate the password using Django's password validation mechanisms.
4. Create the user using Django's built-in user creation functionality.
5. Store the account in SQLite.
6. Provide a clear success or error message.

After successful signup, the user may be directed to the login page.

Automatic login immediately after signup is not required.

---

## 8. Login Requirements

Provide a login page containing:

- Username
- Password

The login process should use Django's built-in authentication mechanisms.

For valid credentials:

    Login
      ↓
    Django authentication
      ↓
    Authenticated session
      ↓
    Application access

For invalid credentials:

- Do not create an authenticated session.
- Display a clear user-friendly error message.
- Do not reveal whether the username or password was specifically incorrect.

---

## 9. Logout Requirements

Authenticated users must have a logout option available from the application interface.

Logout should use Django's built-in logout/session functionality.

After logout:

- The authenticated session should be terminated.
- Protected application pages should no longer be accessible without logging in again.

---

## 10. Protected Application Area

The existing assessment dashboard should require authentication.

Current assessment entry point:

    /assessment/

Expected behavior:

### Unauthenticated user

    User
      ↓
    /assessment/
      ↓
    Redirect to Login
      ↓
    Login
      ↓
    Assessment Dashboard

### Authenticated user

    User
      ↓
    /assessment/
      ↓
    Assessment Dashboard

Authentication should protect access to the assessment application without changing the existing ZAP workflow.

---

## 11. Landing Page Requirements

The existing landing page should remain functionally intact.

Authentication-related navigation may be added to the landing page.

The landing page should provide access to:

- Login
- Sign Up

The existing application description and primary call-to-action should remain.

Do not redesign the entire landing page as part of the authentication implementation.

---

## 12. Authenticated Dashboard Requirements

After successful login, the existing assessment dashboard should remain available.

The dashboard should provide a simple logout option.

No user profile page is required.

No account-management dashboard is required.

No display of user-specific assessment history is required.

---

## 13. Assessment Independence

Authentication must not introduce a relationship between users and assessment sessions.

The existing assessment architecture remains:

    Authenticated User
          ↓
    Assessment Dashboard
          ↓
    Existing Assessment Service
          ↓
    ZAP Client
          ↓
    OWASP ZAP

There should be no:

    User → Assessment

database relationship.

The existing in-memory assessment state remains unchanged.

---

## 14. Existing ZAP Functionality

The authentication implementation must not modify the existing ZAP workflow unless required only to enforce authenticated access to the application.

The following functionality must remain unchanged:

- Target verification
- Spider
- Passive scanning
- Active scanning
- Active scan duration selection
- Active scan stopping
- Alert retrieval
- Alert summary
- Findings
- Report generation
- ZAP API communication
- ZAP API key handling

The ZAP API key must remain server-side and must not be exposed to browser-side JavaScript.

---

## 15. Application Structure

A dedicated Django application named `accounts` is recommended for authentication functionality.

Recommended structure:

    zap-security-poc/
    │
    ├── manage.py
    │
    ├── config/
    │
    ├── assessment/
    │
    ├── accounts/
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── forms.py
    │   ├── urls.py
    │   └── views.py
    │
    ├── templates/
    │   ├── accounts/
    │   │   ├── login.html
    │   │   └── signup.html
    │   │
    │   ├── landing.html
    │   ├── assessment.html
    │   └── base.html
    │
    ├── static/
    │
    ├── docs/
    │
    └── db.sqlite3

The exact structure may be adjusted to match the existing project architecture.

---

## 16. Authentication UI Requirements

The authentication UI should be simple and consistent with the existing Phase 3 visual design.

### Login

The login page should contain:

- Application branding/name
- Username field
- Password field
- Login button
- Link to Sign Up
- Clear validation/error messages

### Signup

The signup page should contain:

- Application branding/name
- Username field
- Password field
- Confirm password field
- Create Account button
- Link to Login
- Clear validation/error messages

### Logout

The existing authenticated application header should contain a simple Logout option.

Avoid adding unnecessary UI components.

---

## 17. Security Requirements

The implementation must:

- Use Django's built-in password hashing.
- Never store plaintext passwords.
- Use Django's built-in authentication/session mechanisms.
- Preserve CSRF protection for authentication forms.
- Validate signup input.
- Validate password confirmation.
- Prevent duplicate usernames.
- Keep the ZAP API key server-side.
- Keep `.env` outside version control.
- Avoid exposing authentication credentials to frontend JavaScript.

Do not implement custom authentication or password hashing.

---

## 18. Session Requirements

Django's normal session mechanism should be used to maintain authenticated login state.

The application does not require custom session management.

Authentication sessions and assessment state are separate.

A Django restart may terminate active runtime assessment state, but existing user accounts must remain stored in SQLite.

---

## 19. Multi-User Requirements

The application does not need to support concurrent users or concurrent assessments.

The application remains a single-user POC from an operational perspective.

Multiple accounts may exist in the database, but only one user is expected to use the application at a time.

No multi-user assessment isolation is required.

---

## 20. Dependencies

Do not add external authentication libraries unless a specific technical requirement makes them necessary.

Use Django's existing authentication functionality.

Do not introduce:

- Django REST Framework
- JWT libraries
- OAuth libraries
- Social authentication libraries
- MySQL drivers
- Redis
- Celery
- Additional authentication services

The goal is a simple and lightweight implementation.

---

## 21. Documentation Precedence

This document is an additive requirement document for authentication.

Where this document conflicts with an authentication-related requirement or assumption in the original six project documents, this document takes precedence.

For all unrelated functionality, the original project documentation remains the source of truth.

The existing ZAP assessment functionality and architecture must not be redesigned as part of this authentication change.

---

## 22. Minimal Acceptance Criteria

Authentication implementation is considered complete when all of the following work:

### Signup

- User can open the signup page.
- User can create an account.
- Duplicate usernames are rejected.
- Invalid passwords are rejected appropriately.
- Account is stored in SQLite.

### Login

- Valid credentials successfully authenticate the user.
- Invalid credentials are rejected.
- Authenticated users can access `/assessment/`.

### Protection

- Unauthenticated users attempting to access `/assessment/` are redirected to login.
- Authenticated users can access the existing dashboard.

### Logout

- Authenticated user can log out.
- After logout, `/assessment/` requires authentication again.

### Persistence

- Stop Django.
- Restart Django.
- Previously created user can still log in.

### Existing POC

- Existing assessment functionality remains available after authentication.
- No user-to-assessment mapping is introduced.
- No changes are required to the existing ZAP workflow.

---

## 23. Testing Strategy

Keep testing minimal.

Perform only the following manual smoke tests:

1. Create a new account.
2. Log in with the new account.
3. Access the assessment dashboard.
4. Log out.
5. Verify the assessment dashboard requires login.
6. Restart Django.
7. Log in again using the previously created account.
8. Verify the existing assessment dashboard still works.

Do not introduce a large automated testing suite for this POC.

---

## 24. Implementation Principle

The authentication layer should be implemented as a small, isolated addition to the existing application.

Primary principle:

    Add authentication.
    Do not redesign the POC.

The implementation should preserve:

- Existing ZAP integration
- Existing assessment workflow
- Existing findings
- Existing reporting
- Existing UI/UX where practical
- Existing project structure
- Existing dependencies

Only the minimum changes required for signup, login, logout, and protected application access should be introduced.