# System Architecture Patterns

## Layered Architecture

### 1. Routes Layer
- **Files**: `src/app/routes/{auth, user, manager}.py`
- **Responsibility**: HTTP request handling, input marshaling, response formatting
- **Pattern**: Flask Blueprints registered with `/api/auth`, `/api/users`,
  `/api/manager` prefixes
- **Security**: `@login_required` decorators, role checks via
  `auth_service.require_roles()`
- **CSRF**: All three blueprints are CSRF-exempt (JSON API; CSRF handled via
  SameSite cookies)
- **Unauthorized handler**: `login_manager.unauthorized_handler` returns
  `{"message": "Authentication required."}` with HTTP 401 (not 302 redirect)

### 2. Services Layer
- **Authentication Service** (`auth.py`) — registration, login (two-step: password
  then email OTP), email verification token checking, account lockout, role-based
  authorization, audit logging integration
- **Security Service** (`security.py`) — Argon2 password hashing, password complexity
  validation (individual regex per rule, no character whitelist), TOTP secret
  generation, email OTP generation
- **Auditing Service** (`auditing.py`) — security event logging (login, role changes,
  unauthorized access), failed login attempt tracking, account lock event logging
- **User Management Service** (`user_management.py`) — user listing and detail
  retrieval, user metadata updates, phone status history querying
- **Validation Service** (`validation.py`) — request payload parsing and validation,
  domain-specific validators (email, phone, IMEI, password, OTP), whitelist-based
  field acceptance, custom exception: `ValidationError`

### 3. Models Layer
- **ORM Models**: SQLAlchemy declarative base with relationships
  - `User`: accounts with password hash, two_factor_secret, email verification
    token, OTP code hash, OTP expiry, password reset token, password reset expiry
  - `PhoneStatusHistory`: immutable audit trail of status changes
  - `AuditLog`: security event tracking
- **Domain Models**: Dataclasses used for validation
  - `RegisterData`, `LoginData`, `OtpData`, `ForgotPasswordData`, `ResetPasswordData`,
    `StatusUpdateData`, `RoleUpdateData`, `UserUpdateData` — post-init validation with
    `ValidationError`
  - `UserProfile`, `PhoneStatusRecord` — domain data validation

### 4. Frontend Layer
- **File**: `src/frontend/src/App.tsx`
- **Pattern**: View state machine — `type View = "loading" | "login" | "register" | "otp" | "dashboard" | "forgot-password" | "reset-password"`
- **Session detection**: `GET /api/users/me` → 401 → switch to `"login"` view
- **Reset token detection**: `useEffect` checks `window.location.search` for `?reset_token=`;
  if found, stores token in state, strips from URL bar, switches to `"reset-password"` view
- **Auth flows**:
  - Login step 1: `POST /api/auth/login` → 202 + `requires_otp` → transition to `"otp"` view
  - Login step 2: `POST /api/auth/verify-otp` → 200 → `loadProfile()` → `"dashboard"` view
  - Register: `POST /api/auth/register` → 201 → info notification → `"login"` view
  - Forgot password: `POST /api/auth/forgot-password` → 200 → info notification → `"login"` view
  - Reset password: `POST /api/auth/reset-password` → 200 → info notification → `"login"` view
  - Logout: `POST /api/auth/logout` → `"login"` view
- **State**: `pendingUsername` (OTP flow), `forgotEmail`, `resetToken`, `resetNewPassword`
- **Sub-components**: `AuthCard` (with optional `footer` prop), `AuthField`, `Dashboard`,
  `ManagedUsersSection`, `UserDetailCard` — each focused on a single view section
- **Dev proxy**: Vite proxies `/api` → `http://localhost:5001` (not 5000; AirPlay
  on macOS occupies port 5000)

## Authentication Flow (Two-Step Email OTP)

```
User enters username + password
    ↓
POST /api/auth/login
    ↓
AuthService.authenticate() — Argon2 password check, lockout check
    ↓
Check user.is_email_verified — 403 if not verified
    ↓
SecurityService.generate_email_otp() → (otp, otp_hash)
Store otp_code_hash + otp_expires_at on user row
Flask-Mail sends OTP to user's email
    ↓
Return 202 + {"requires_otp": true}
    ↓ (user reads email, enters OTP)
POST /api/auth/verify-otp
    ↓
AuthService.verify_login_otp()
  - Lockout check
  - Check OTP expiry (10 min)
  - Argon2 verify(otp_code_hash, submitted_otp)
  - Clear OTP fields; clear failed login counter
    ↓
login_user(user) → Flask-Login session
Return 200
```

## Database Migration Pattern (Alembic)
- `alembic/env.py` — imports `src.app.extensions.db` and `src.app.models` to
  populate `db.metadata` without Flask app context; reads `DATABASE_URL` env var
- `alembic upgrade head` via `make migrate`
- Migration 001: `alembic/versions/001_initial_schema.py` — creates all tables
  and PostgreSQL enum types; `downgrade()` drops enums explicitly
- Migration 002: `alembic/versions/002_add_email_otp_fields.py` — adds
  `otp_code_hash` and `otp_expires_at` to users table
- Migration 003: `alembic/versions/003_add_password_reset_fields.py` — adds
  `password_reset_token` and `password_reset_expires_at` to users table

## Security Patterns

### Defense in Depth
1. **Input Validation**: Whitelist approach, type coercion, bounds checking
   (validation.py); also checked inside SecurityService as a second layer
2. **Authentication**: Argon2 password hashing; email-OTP 2FA (mandatory, not optional)
3. **Authorization**: Role-based access control enforced at service layer
4. **Auditing**: All sensitive operations logged with actor, resource, and action
5. **Communication**: HTTPS, HSTS, CSRF tokens, SameSite cookies (configurable)
6. **CI scanning**: bandit (SAST), pip-audit (dependency CVEs)

### Password Validation — Two-Layer Architecture
Both layers must agree. They use equivalent individual regex checks:
- **validation.py** (`_validate_password_complexity`) — user-facing layer, raises
  `ValidationError` with specific messages before the service layer is called
- **SecurityService** (`validate_password_complexity`) — defense-in-depth layer,
  raises `PasswordComplexityError`; four compiled patterns: `_UPPERCASE`,
  `_LOWERCASE`, `_DIGIT`, `_SPECIAL_CHARS`
- **Critical**: Neither layer has a character whitelist — any character is permitted
  as long as the four required types are present. (Bug fixed 2026-06-18 — the
  previous `[a-zA-Z\d@$!%*?&]{8,128}` whitelist was removed.)

### OTP Security
- Generated with `secrets.randbelow(1_000_000)` (CSPRNG, zero-padded to 6 digits)
- Stored as Argon2 hash (same library as passwords) — plaintext never persisted
- Failures tracked against the same lockout counter as password failures
- Cleared from DB after successful verification or expiry check

### Fail-Safe Defaults
- Session cookies: HTTPONLY, SAMESITE by default
- CSRF protection: Enabled (blueprints exempted since they're JSON API)
- Rate limiting: In-memory tracking (configurable for production)
- Account lockout: Automatic after 5 combined failed attempts (password + OTP)
- Password policy: Strict complexity requirements enforced at both validation layers
- Email 2FA: Mandatory on every login (no skip option)

## Exception Hierarchy
```
Exception
├── ValidationError (input validation failures — validation.py)
├── AuthError (authentication failures)
│   └── AccountLockedError (account lockout — HTTP 429)
├── AuthorizationError (permission denied — HTTP 403)
├── HashingError (password hashing or verification failures)
├── PasswordComplexityError (password policy violations — security.py)
├── UserManagementError (user management failures)
│   └── UserNotFoundError (user lookup failures — HTTP 404)
└── AuditingError (audit logging failures)
```

## Request/Response Pattern
```python
@route
def endpoint():
    try:
        # 1. Validate input
        data = validation_service.parse_payload(request.get_json())
        # 2. Check authorization
        auth_service.require_roles(current_user, [Role.ADMIN])
        # 3. Execute business logic
        result = service.perform_action(data)
        # 4. Return formatted response
        return {"result": result}, 200
    except ValidationError as e:
        return validation_error_response(str(e))
    except AuthorizationError as e:
        return error_response(str(e), 403)
    except AuthError as e:
        return error_response(str(e), 401)
```

## Login Route — Special Two-Step Pattern
```python
@auth_bp.post("/login")
def login():
    # Step 1: Validate credentials
    user = auth_service.authenticate(username, password)  # raises on failure
    # Step 2: Enforce email verification
    if not user.is_email_verified:
        return error_response("Email address not verified...", 403)
    # Step 3: Generate + send OTP (session NOT created yet)
    auth_service.generate_and_send_login_otp(user)
    return {"requires_otp": True}, 202

@auth_bp.post("/verify-otp")
def verify_otp():
    user = auth_service.verify_login_otp(username, otp)  # raises on failure
    login_user(user)  # Flask-Login session created HERE
    return {"message": "Login successful."}, 200
```

## Testing Patterns
- **Unit Tests**: Service classes tested in isolation (SecurityService, ValidationService)
- **Integration Tests**: End-to-end flows through routes with in-memory SQLite test DB
- **Fixtures**: `app` (Flask app with SQLite) and `client` (FlaskClient) in
  `tests/conftest.py`; each test gets a fresh DB via `db.drop_all()` teardown
- **OTP Capture**: `patch("src.app.services.auth.send_login_otp")` then
  `mock.call_args[0][1]` captures the plaintext OTP (second positional arg)
- **Email Suppress**: `MAIL_SUPPRESS_SEND=app_config.testing` prevents real SMTP in tests
- **Parametrize**: Used in `test_password_verification.py` for extended-char matrix
- **Coverage targets**: 80%+ overall; critical security paths have explicit tests
  for both happy path and all error branches

## CI/CD Pattern (GitHub Actions)
```
Push/PR → backend job (lint → format → typecheck → test → bandit → pip-audit)
        → frontend job (npm ci → tsc --noEmit)
```
- Test artifacts (junit.xml, coverage.xml) uploaded on every run
- `make ci` runs the same checks locally
