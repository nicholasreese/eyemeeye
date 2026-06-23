## 2026-06-24 — Forgot Password / Password Reset Implemented

### Forgot Password Feature
Full end-to-end password reset flow added across backend and frontend.

**Reset flow:**
1. User clicks "Forgot password?" on login → `POST /api/auth/forgot-password` with `{email}`
2. Backend looks up user by email, generates a `secrets.token_urlsafe(32)` token, stores it
   plaintext (same pattern as email verification token), sets 1-hour expiry, sends email.
   Always returns HTTP 200 — unknown emails silently no-op to avoid account enumeration.
3. Email contains a link `{host}/?reset_token=TOKEN`
4. Frontend detects `?reset_token=` in `window.location.search` on initial load, strips it
   from the URL bar, and switches to the `"reset-password"` view
5. User enters new password → `POST /api/auth/reset-password` with `{token, new_password}`
6. Backend finds user by token, checks expiry, hashes new password, clears token fields → 200

### Backend Changes
- `User` model gains: `password_reset_token (String 64, nullable)`,
  `password_reset_expires_at (DateTime, nullable)`
- Alembic migration `003_add_password_reset_fields.py`
- `SecurityService.generate_reset_token()` — `secrets.token_urlsafe(32)`
- `AuthService.request_password_reset(email)` — silently no-ops on unknown email
- `AuthService.reset_password(token, new_password)` — validates expiry, updates password hash,
  clears token; raises `AuthError` on invalid/expired token
- `send_password_reset_email(email, token)` added to `email.py` — builds link from
  `request.host_url` (frontend SPA URL, not a backend API path)
- `ForgotPasswordData`, `ResetPasswordData` dataclasses + parsers added to `validation.py`
- `POST /api/auth/forgot-password` and `POST /api/auth/reset-password` routes added to
  `auth` blueprint

### Frontend Changes (App.tsx)
- `View` type extended: `"forgot-password"` and `"reset-password"` added
- Initial `useEffect` checks `window.location.search` for `?reset_token=`; if found, stores
  token in state, strips it from URL bar, and switches to `"reset-password"` view
- States added: `forgotEmail`, `resetToken`, `resetNewPassword`
- `handleForgotPassword` and `handleResetPassword` handlers added
- "Forgot password?" link added to login view (below submit button via `AuthCard` `footer` prop)
- `forgot-password` view: email input + "Send Reset Link" submit + "Back to sign in"
- `reset-password` view: new password input + "Reset Password" submit + "Back to sign in"
- `AuthCard` component extended with optional `footer` prop

### Tests (tests/test_password_reset.py — 13 new tests, all passing)
- `POST /forgot-password`: registered email sends email, unknown email returns 200 without
  sending, invalid email returns 400, missing email returns 400, token stored on user
- `POST /reset-password`: valid token succeeds, token cleared after use, invalid token → 400,
  expired token → 400, token cannot be reused, weak password → 400, missing fields → 400,
  new password works for subsequent login (end-to-end)

### Overall Status (2026-06-24)
- **Total Tests**: 112 (passing: 112, failing: 0)
  - test_auth.py: 14, test_config.py: 3, test_email.py: 1, test_manager.py: 5,
    test_models.py: 4, test_password_reset.py: 13, test_password_verification.py: 38,
    test_responses.py: 2, test_security.py: 20, test_user.py: 3, test_validation.py: 9
- **Migrations**: 3 total (001 initial schema, 002 OTP fields, 003 password reset fields)

---

## 2026-06-23 — Email-Based 2FA Fully Implemented

### Two-Factor Authentication
- **Login flow** changed from single-step (password → session) to two-step:
  1. `POST /api/auth/login` → 202 + `requires_otp: true` (sends OTP email)
  2. `POST /api/auth/verify-otp` → 200 + session created
- **Email verification enforced**: login step 1 returns 403 if `is_email_verified` is false
- **New endpoints**: `POST /api/auth/verify-otp`, `GET /api/auth/verify-email`
- **OTP delivery**: Flask-Mail sends 6-digit codes; codes expire after 10 minutes;
  hashed with Argon2 (same as passwords) before storage
- **OTP failure tracking**: failed OTP attempts count against the same lockout counter
  as password failures (5 combined failures → HTTP 429)
- **TOTP removed**: old pyotp-based optional TOTP login field removed from login form
  and route handling

### Backend Changes
- `Flask-Mail==0.10.0` added to `requirements.txt`
- `mail` extension added to `extensions.py`; `MAIL_*` config + `MAIL_SUPPRESS_SEND`
  added to app factory
- `SecurityService.generate_email_otp()` → `(otp: str, otp_hash: str)`
- `AuthService` gains: `generate_and_send_login_otp`, `verify_login_otp`,
  `verify_email_token`
- `ValidationService` gains: `OtpData` dataclass, `parse_otp_payload()`
- `User` model gains: `otp_code_hash (String, nullable)`, `otp_expires_at (DateTime, nullable)`
- Alembic migration `002_add_email_otp_fields.py`
- `email.py` rewritten from stub to Flask-Mail implementation; logs INFO before sending

### Frontend Changes (App.tsx)
- `LoginForm.token` field removed (TOTP gone)
- `View` union type gains `"otp"` state
- `pendingUsername` and `otpCode` state variables added
- `handleLogin` now transitions to `"otp"` on `requires_otp: true` response
- `handleVerifyOtp` handler added — POSTs OTP, loads profile on success
- OTP view rendered: "Check Your Email" heading, 6-digit numeric input, submit,
  "Back to sign in" link

### Test Suite (99 tests, all passing)
- All test helpers that used TOTP-based login updated to:
  1. Verify email after registration (read token from DB, call verify-email endpoint)
  2. Mock `src.app.services.auth.send_login_otp` to capture the OTP
  3. Call `POST /verify-otp` with captured OTP to complete login
- `test_email.py` rewritten: `send_verification_email` tested by mocking `mail.send`
  inside `app.test_request_context()` and asserting `mail.send` called once
- `test_validation.py`: removed stale `token=None` kwarg from `LoginData()`
- `test_password_verification.py`: success login assertions changed 200 → 202

---

## 2026-06-20 — UI Polish & TypeScript Fixes

### Frontend Branding
- Logo (`logo2.svg`) added centered at the top of all pages via `src/frontend/public/images/`
  — height 144px (80% larger than initial 80px); wrapper margin-bottom 0.3rem (80% tighter)
- Page heading changed from "Phone Management Portal" to "EyeMeEye"
- Tagline "Stop Mobile Phone Theft" added below heading at 1.6rem (20% smaller), centered

### TypeScript / Tooling
- Replaced generic `updateField<T>` helper (caused persistent TS2345 inference failures)
  with two concrete handlers: `updateLoginForm` and `updateRegisterForm`
- Removed `"ignoreDeprecations": "6.0"` from `tsconfig.json` (invalid for TS 5.4, caused TS5103)
- `tsc --noEmit` now passes with zero errors

---

## 2026-06-18 — All Phases Complete

### Phase 1: User Authentication ✅ COMPLETE
- User registration and login with email verification (token generated, email sent)
- Account lockout after 5 failed attempts (combined password + OTP failures)
- Secure password hashing (Argon2)
- Password complexity: 8–128 chars, uppercase, lowercase, digit, special (`@$!%*?&`)
  — **any other characters also permitted** (bug fix applied 2026-06-18)
- Test coverage: auth-focused integration tests in `tests/test_auth.py`

### Phase 2: User Management ✅ COMPLETE
- Manager/admin user viewing and editing endpoints
- Phone status history tracking and querying (4 states: online, sold, stolen, disposed)
- Role-based access control (USER, MANAGER, ADMIN)
- Admin can update email, phone, IMEI, role via PATCH endpoint
- Test coverage: `tests/test_manager.py`, `tests/test_user.py`

### Phase 3: Security & Best Practices ✅ COMPLETE
- Enhanced password complexity validation (per-rule checks, specific error messages)
- Account lockout mechanism (5 failed attempts → HTTP 429)
- Comprehensive security audit logging (all auth events tracked in `audit_logs` table)
- Input validation hardening (username, email, phone, IMEI bounds)
- Secure communication support (HTTPS, HSTS, CSRF, SameSite cookies via Talisman)
- Authorization access control logging (unauthorized access attempts logged)
- Test coverage: `tests/test_security.py`, `tests/test_validation.py`

### Phase 4: Frontend + Documentation + CI ✅ COMPLETE

#### React Frontend
- Single-page portal at `src/frontend/`
- **View state machine**: loading → login → [otp] → dashboard (or register → login → ...)
- Login form: username, password (OTP code collected on dedicated OTP screen)
- OTP form: 6-digit input, pending username displayed, back link
- Register form: username, email, phone number, IMEI, password (with hint)
- Dashboard: profile display, status update form, status history
- Manager panel (manager/admin only): user table with View action
- User detail card: profile, status history, admin edit form (admin only)
- Sign-out button clears session and returns to login
- Session detection: unauthenticated requests return 401 JSON (not 302 redirect)

#### Documentation (Sphinx)
- `docs/conf.py`: theme, author, version, viewcode, intersphinx extensions
- `docs/index.rst`: role/status overview tables, security highlights
- `docs/installation.rst`: setup, venv, DB migration commands, troubleshooting
- `docs/configuration.rst`: full env var table, password policy, lockout policy
- `docs/usage.rst`: REST API reference with example requests, portal guide
- `docs/api.rst`: autodoc for all modules (config, models, all services, all routes)

#### CI/CD (GitHub Actions)
- `.github/workflows/ci.yml`
- **backend job**: lint, format-check, mypy, pytest (JUnit + coverage XML artifacts),
  bandit (SAST), pip-audit (dependency CVE scan)
- **frontend job**: npm ci, tsc --noEmit

#### Database Migrations (Alembic)
- `alembic.ini`, `alembic/env.py` (Flask-SQLAlchemy integration)
- `alembic/versions/001_initial_schema.py`: creates users, phone_status_history,
  audit_logs tables with correct enum types, FK cascades, and downgrade path

#### Bug Fix: Password Verification (2026-06-18)
- `SecurityService._PASSWORD_PATTERN` had a character whitelist `[a-zA-Z\d@$!%*?&]`
  that silently rejected valid passwords with `_`, `-`, space, `#`, `^`, etc.
- Fixed by replacing the single regex with four individual compiled patterns
- 38 new tests added in `tests/test_password_verification.py`

### Overall Status (2026-06-23)
- **Total Tests**: 99 (passing: 99, failing: 0)
  - test_auth.py: 14, test_config.py: 3, test_email.py: 1, test_manager.py: 5,
    test_models.py: 4, test_password_verification.py: 38, test_responses.py: 2,
    test_security.py: 20, test_user.py: 3, test_validation.py: 9
- **Type Checking**: mypy strict configured in pyproject.toml; `tsc --noEmit` zero errors
- **Linting**: ruff configured with formatting/lint targets
- **Docs**: Sphinx HTML build available (`make docs`)
- **Migrations**: Alembic ready (`make migrate`); two migrations (001, 002)
- **Security scanning**: bandit + pip-audit available (`make security`)
