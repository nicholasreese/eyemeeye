## Current Status: All Four Phases Complete — Password Reset Added

### What Was Just Done (2026-06-24)

#### Forgot Password / Password Reset Flow
Full end-to-end password reset feature added to both backend and frontend.

**Reset flow:**
1. User clicks "Forgot password?" on login → `forgot-password` view
2. `POST /api/auth/forgot-password` with `{email}` — always returns HTTP 200 (no account enumeration);
   if email is registered, stores a `secrets.token_urlsafe(32)` token + 1-hour expiry, sends email
3. Email link: `{host}/?reset_token=TOKEN` → SPA detects on load, strips from URL bar, shows
   `reset-password` view
4. `POST /api/auth/reset-password` with `{token, new_password}` — validates expiry, updates hash,
   clears token; invalid/expired token → HTTP 400

**Backend components added:**
- `User.password_reset_token` and `User.password_reset_expires_at` columns
- Alembic migration `003_add_password_reset_fields.py`
- `SecurityService.generate_reset_token()` — `secrets.token_urlsafe(32)`
- `AuthService.request_password_reset(email)` and `AuthService.reset_password(token, new_password)`
- `send_password_reset_email(email, token)` in `email.py`
- `ForgotPasswordData`, `ResetPasswordData` dataclasses + parsers in `validation.py`
- `POST /api/auth/forgot-password` and `POST /api/auth/reset-password` routes

**Frontend components added (App.tsx):**
- `View` type: `"forgot-password"` and `"reset-password"` added
- `useEffect` checks `?reset_token=` on page load; strips param, stores in state
- `forgotEmail`, `resetToken`, `resetNewPassword` states
- `handleForgotPassword`, `handleResetPassword` handlers
- "Forgot password?" link on login view (via `AuthCard` optional `footer` prop)
- `forgot-password` and `reset-password` view JSX

**Tests:** 13 new tests in `tests/test_password_reset.py` — all passing (112 total)

---

### What Was Done (2026-06-23)

#### Email-Based Two-Factor Authentication (2FA)
Full end-to-end 2FA using email OTP implemented across backend and frontend.

**Login flow changed from single-step to two-step:**
1. `POST /api/auth/login` — validates password, checks email is verified, generates a
   6-digit OTP, emails it to the user; returns HTTP 202 + `{"requires_otp": true}`
2. `POST /api/auth/verify-otp` — verifies the hashed OTP, creates the authenticated
   session; returns HTTP 200

**Email verification now enforced:**
- Registration issues a verification token; `GET /api/auth/verify-email?token=<tok>`
  marks `is_email_verified = true`
- Login step 1 returns HTTP 403 if email not yet verified

**New backend components:**
- `Flask-Mail==0.10.0` added to `requirements.txt`
- `mail = Mail()` extension in `src/app/extensions.py`; initialized in app factory
- `MAIL_*` config keys + `MAIL_SUPPRESS_SEND=testing` in `src/app/__init__.py`
- `send_login_otp(email, otp)` and `send_verification_email(email, token)` in
  `src/app/utils/email.py` using Flask-Mail (suppressed in tests)
- `generate_email_otp() → (otp, otp_hash)` added to `SecurityService`
- `generate_and_send_login_otp(user)`, `verify_login_otp(username, otp)`,
  `verify_email_token(token)` added to `AuthService`
- `OtpData` dataclass + `parse_otp_payload()` added to `ValidationService`
- `User.otp_code_hash`, `User.otp_expires_at` columns added to model
- Alembic migration `002_add_email_otp_fields.py`

**New frontend components (App.tsx):**
- `View` type extended: `"loading" | "login" | "register" | "otp" | "dashboard"`
- States: `pendingUsername`, `otpCode`
- `handleLogin` updated: detects `requires_otp: true`, transitions to `"otp"` view
- `handleVerifyOtp`: POSTs to `/api/auth/verify-otp`, calls `loadProfile()` on success
- OTP view JSX: "Check Your Email" form, 6-digit numeric input, "Back to sign in" link
- Login form cleaned up: removed obsolete TOTP `token` field
- `LoginForm` interface: `token` field removed

**Tests updated (99 tests, all passing):**
- `test_auth.py`: 14 tests — mock patch corrected to `src.app.services.auth.send_login_otp`
- `test_email.py`: rewritten — `send_verification_email` tested with `mail.send` mocked
  within a proper app context
- `test_manager.py`, `test_user.py`, `test_security.py`: helpers updated to verify
  email after registration and use the new two-step OTP login flow
- `test_password_verification.py`: `_register` helper verifies email; success
  assertions changed from HTTP 200 → 202
- `test_validation.py`: removed stale `token=None` kwarg from `LoginData` call

---

### What Was Done (2026-06-20)

#### Frontend Branding & UI Polish
- **Logo added**: `logo2.svg` in `src/frontend/public/images/`; height 144px (80% larger
  than 80px); wrapper margin-bottom 0.3rem (80% tighter)
- **Heading renamed**: "Phone Management Portal" → "EyeMeEye"
- **Tagline added**: "Stop Mobile Phone Theft" at 1.6rem, centered, muted colour

#### TypeScript Fixes
- Replaced generic `updateField<T>` (TS2345 errors) with two concrete handlers
- Removed `"ignoreDeprecations": "6.0"` from tsconfig.json (invalid for TS 5.4)
- `tsc --noEmit` passes with zero errors

---

### Development Servers
- Flask backend: `http://localhost:5001`
  (`SECRET_KEY="dev-secret-key-for-testing" DATABASE_URL="sqlite:///app.db"`)
- Vite frontend: `http://localhost:5173` (proxies `/api` → 5001)
- Note: `.env` has `SECRET_KEY=your_secret_key` (15 chars — below 16-char minimum).
  Must override via env var for local dev.

### Known Remaining Issues
- In-memory rate limiter not suitable for multi-process production (use Redis)
- Account unlock requires manual admin intervention (no expiry timer, no unlock endpoint)
- No admin UI for viewing audit logs
- Sphinx produces HTML only; PDF requires LaTeX toolchain
- venv in repo is Linux-built (x86_64 ELF); macOS requires system Python (3.13)

### Immediate Next Steps (if continuing)
- Add Redis-backed rate limiter for production
- Add admin audit log viewer endpoint + UI panel
- Add account unlock endpoint for admins
- PDF documentation output (`make docs` currently generates HTML only)
