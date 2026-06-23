# Product Context - Phone Lifecycle Management

## Problem Statement
Users need a centralized, secure way to:
- Track their phone's lifecycle status (operational, sold, stolen, disposed)
- Authorize third-party managers to view their phone information
- Allow administrators to manage user accounts and enforce policies
- Maintain an audit trail of all status changes and administrative actions

## User Personas

### Individual User (USER role)
- Registers with username, email, phone number, IMEI, and password
- Receives an email verification link; must verify before logging in
- Logs in via two-step flow: password → email OTP (6-digit code, 10-min expiry)
- Updates personal phone status (online → sold → stolen → disposed)
- Views own status history

### Manager (MANAGER role)
- Views all user profiles and phone status histories (read-only)
- Supports third-party service providers or enterprise managers
- Cannot modify user data or settings
- Accesses user list and detail via manager endpoints

### Administrator (ADMIN role)
- Full access to all user accounts and data
- Can promote/demote user roles via PATCH endpoint
- Can edit user details (email, phone, IMEI)
- All role changes written to audit log
- Manages security policies (lockout enforcement through audit log review)

## Key Requirements Met

### Security Requirements
- ✅ Password complexity enforcement (8–128 chars, mixed case, digits, special chars)
  — any additional characters also permitted (fixed 2026-06-18)
- ✅ Account lockout mechanism (5 consecutive failed attempts → HTTP 429; counts
  both password failures and OTP failures)
- ✅ Email-based two-factor authentication (mandatory — a 6-digit OTP is emailed
  on every login; TOTP is no longer used)
- ✅ Email verification enforced — login blocked (403) until email confirmed
- ✅ Secure communication (HTTPS/HSTS support via Flask-Talisman)
- ✅ CSRF protection on all state-changing operations
- ✅ Comprehensive audit logging (login, role changes, unauthorized access)
- ✅ Security scanning in CI (bandit SAST, pip-audit CVE scan)

### Functional Requirements
- ✅ User registration with mandatory email verification (Flask-Mail sends real email)
- ✅ Secure two-step login (password check → email OTP verification)
- ✅ Phone status management (4 states: online, sold, stolen, disposed)
- ✅ User profile display (username, email, phone, IMEI, role)
- ✅ Manager view-only access and user status history
- ✅ Admin user management capabilities (profile + role updates)
- ✅ Role-based access control
- ✅ Frontend portal: login, OTP verification, register, dashboard, manager panel,
  admin edit form

### Quality Requirements
- ✅ Strict typing (mypy --strict configured; tsc --noEmit zero errors)
- ✅ 99 test cases across 10 test modules — all passing
- ✅ All linting checks passing (ruff)
- ✅ Google-style docstrings on all functions/classes
- ✅ Comprehensive error handling with specific exceptions
- ✅ Structured logging with context metadata

## Branding
- **Product name**: EyeMeEye (displayed as `<h1>` on all pages)
- **Tagline**: "Stop Mobile Phone Theft" (displayed below heading on all pages)
- **Logo**: `logo2.svg` centered above the heading on every page

## Success Metrics (Current State)
- 99 passing tests, 0 failures
- All password character sets now accepted (underscore, hyphen, space, etc.)
- Two-step login with email OTP enforced for all users
- Email verification required before first login
- React UI: login → OTP → dashboard state machine
- CI pipeline enforces lint, typecheck, test, and security scan on every push
- Alembic handles schema migrations (two migrations: initial schema + OTP fields)
- Sphinx generates HTML API docs and usage guides

## Known Limitations
- Account unlock requires manual DB/admin intervention (no expiry timer, no endpoint)
- No password reset / account recovery flow
- Rate limiter uses in-memory storage (not suitable for multi-process production)
- No admin UI for viewing audit logs
