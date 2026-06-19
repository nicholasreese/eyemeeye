## Current Status: All Four Phases Complete — UI Polish

### What Was Just Done (2026-06-20)

#### Frontend Branding & UI Polish
- **Logo added**: `logo2.svg` copied to `src/frontend/public/images/` (Vite static dir)
  and rendered as `<img className="site-logo">` centered at the top of every page
  (loading, login, register, dashboard — it's in the root `<main>` shell).
  CSS: `height: 144px; width: auto` (original 80px, scaled 80% bigger).
  Wrapper margin-bottom reduced to `0.3rem` (was `1.5rem`, reduced 80%).
- **Heading renamed**: "Phone Management Portal" → "EyeMeEye" (`<h1 className="page-title">`)
- **Tagline added**: "Stop Mobile Phone Theft" as `<p className="page-tagline">` immediately
  below the heading; font-size `1.6rem` (20% smaller than the `2rem` h1); centered;
  muted colour (`#4a5568`).
- **Heading centered**: `.page-title` now has `text-align: center`.

#### TypeScript Fixes
- **`updateField` generic helper removed**: The `<T extends Record<string, string>>` generic
  was causing persistent TS2345 inference errors at every call site. Replaced with two
  concrete handlers: `updateLoginForm` and `updateRegisterForm` (each casts result `as T`
  internally). All 8 call sites updated.
- **`tsconfig.json` fix**: Removed `"ignoreDeprecations": "6.0"` — that flag requires TS 6+
  but the project uses TS 5.4. Caused TS5103 error on `tsc --noEmit`.
- `tsc --noEmit` now passes with **zero errors**.

#### Dev Servers (current session)
- Flask backend: `http://localhost:5001`
  (`SECRET_KEY="dev-secret-key-for-testing" DATABASE_URL="sqlite:///app.db"`)
- Vite frontend: `http://localhost:5174` (proxies `/api` → 5001)
  (5174 because 5173 was already bound from a prior session)

---

### What Was Just Done (2026-06-18)

#### Phase 4 Gap Closure
- ✅ **React login/register UI** — App.tsx fully rewritten with a `View` state machine
  (`loading → login → dashboard`, or `register → login → dashboard`). Session
  detection via `/api/users/me` returning 401. Sign-out button added. App split into
  focused sub-components: `AuthCard`, `AuthField`, `Dashboard`, `ManagedUsersSection`,
  `UserDetailCard`.
- ✅ **CI/CD pipeline** — `.github/workflows/ci.yml` with separate `backend` and
  `frontend` jobs. Backend: ruff lint + format-check, mypy, pytest with JUnit/coverage
  XML artifacts, bandit, pip-audit. Frontend: npm ci + tsc --noEmit.
- ✅ **Alembic migrations** — `alembic.ini`, `alembic/env.py` (Flask-SQLAlchemy
  integration, reads `DATABASE_URL` env var), `alembic/script.py.mako`,
  `alembic/versions/001_initial_schema.py` (creates all three tables with enum types
  and FK cascade; downgrade drops PostgreSQL enums).
- ✅ **Sphinx docs expanded** — `docs/conf.py` (theme, author, version, viewcode,
  intersphinx), `docs/index.rst` (role/status tables, security overview),
  `docs/installation.rst`, `docs/configuration.rst` (env var table, lockout/password
  policies), `docs/usage.rst` (REST API reference, portal walkthrough, 2FA setup),
  `docs/api.rst` (fixed module paths, added missing modules).
- ✅ **Tooling updates** — `requirements.txt` gains alembic, bandit, pip-audit (sorted
  alphabetically). Makefile gains `security`, `migrate`, `ci` targets.

#### Bug Fix — Password Verification
- **Root cause**: `SecurityService._PASSWORD_PATTERN` ended with
  `[a-zA-Z\d@$!%*?&]{8,128}$` — a silent character whitelist that rejected passwords
  containing `_`, `-`, space, `#`, `^`, `(`, `.`, etc. with the misleading error
  "Password must contain uppercase, lowercase, digit, and special character". The
  `validation.py` layer had no such whitelist, so passwords passed the first check but
  failed the second.
- **Fix**: Removed `_PASSWORD_PATTERN` from SecurityService; replaced with four
  individual compiled regexes (one per rule) matching `validation.py`'s approach.
  Each rule now produces a specific, accurate error message. Also removed
  `# pragma: no cover` from `VerifyMismatchError` handler (now tested).
- **Flask unauthorized handler**: Added `login_manager.unauthorized_handler` returning
  `{"message": "Authentication required."}` with 401, so React fetch detects
  unauthenticated state correctly (instead of following a 302 redirect).
- **vite.config.ts**: Proxy changed from port 5000 to 5001 (5000 is AirPlay on macOS).

#### New Tests
- `tests/test_password_verification.py` — 38 new tests in 5 classes:
  `TestHashPassword`, `TestVerifyPassword`, `TestComplexityErrorMessages`,
  `TestExtendedCharacterPasswords`, `TestRegistrationLoginRoundTrip`.
- Total test suite: **93 tests, 93 passing**.

### Development Servers (started in this session)
- Flask backend: `http://localhost:5001`
  (started with `SECRET_KEY=dev-secret-key-for-testing DATABASE_URL=sqlite:///app.db`)
- Vite frontend: `http://localhost:5173` (proxies `/api` → 5001)
- Note: `.env` has `SECRET_KEY=your_secret_key` which is 15 chars — below the 16-char
  minimum. Must set `SECRET_KEY` via env var when starting Flask locally.

### Known Remaining Issues
- `.env` placeholder SECRET_KEY is too short (15 chars, minimum is 16) — must override
  via env var for local dev
- In-memory rate limiter should be replaced with Redis for production
- Account unlock requires manual admin intervention (no UI or automated expiry)
- 2FA is optional (no enforce-2FA flag per user) — by design for current MVP
- No account recovery / password reset flow

### Immediate Next Steps (if continuing)
- Add a `/api/auth/verify-email/<token>` endpoint and wire up email verification status
- Add password reset / account recovery endpoint
- Add Redis-backed rate limiter for production
- Add admin audit log viewer endpoint + UI panel
- PDF documentation output (`make docs` currently generates HTML only)
- Add account unlock endpoint for admins
