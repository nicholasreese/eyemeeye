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
- **Authentication Service** (`auth.py`) — registration, login, password verification,
  TOTP verification, account lockout checking, role-based authorization, audit
  logging integration
- **Security Service** (`security.py`) — Argon2 password hashing, password complexity
  validation (individual regex per rule, no character whitelist), TOTP secret
  generation
- **Auditing Service** (`auditing.py`) — security event logging (login, role changes,
  unauthorized access), failed login attempt tracking, account lock event logging
- **User Management Service** (`user_management.py`) — user listing and detail
  retrieval, user metadata updates, phone status history querying
- **Validation Service** (`validation.py`) — request payload parsing and validation,
  domain-specific validators (email, phone, IMEI, password), whitelist-based field
  acceptance, custom exception: `ValidationError`

### 3. Models Layer
- **ORM Models**: SQLAlchemy declarative base with relationships
  - `User`: accounts with password hash, 2FA secret, email verification token
  - `PhoneStatusHistory`: immutable audit trail of status changes
  - `AuditLog`: security event tracking
- **Domain Models**: Dataclasses used for validation
  - `RegisterData`, `LoginData`, `StatusUpdateData`, `RoleUpdateData`,
    `UserUpdateData` — post-init validation with `ValidationError`
  - `UserProfile`, `PhoneStatusRecord` — domain data validation

### 4. Frontend Layer
- **File**: `src/frontend/src/App.tsx`
- **Pattern**: View state machine — `type View = "loading" | "login" | "register" | "dashboard"`
- **Session detection**: `GET /api/users/me` → 401 → switch to `"login"` view
- **Auth flows**: Login (`POST /api/auth/login`), Register (`POST /api/auth/register`),
  Logout (`POST /api/auth/logout`)
- **Sub-components**: `AuthCard`, `AuthField`, `Dashboard`, `ManagedUsersSection`,
  `UserDetailCard` — each focused on a single view section
- **Dev proxy**: Vite proxies `/api` → `http://localhost:5001` (not 5000; AirPlay
  on macOS occupies port 5000)

## Database Migration Pattern (Alembic)
- `alembic/env.py` — imports `src.app.extensions.db` and `src.app.models` to
  populate `db.metadata` without Flask app context; reads `DATABASE_URL` env var
- `alembic upgrade head` via `make migrate`
- Initial migration: `alembic/versions/001_initial_schema.py` — creates all tables
  and PostgreSQL enum types; `downgrade()` drops enums explicitly

## Security Patterns

### Defense in Depth
1. **Input Validation**: Whitelist approach, type coercion, bounds checking
   (validation.py); also checked inside SecurityService as a second layer
2. **Authentication**: Argon2 password hashing, TOTP-based 2FA (optional)
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

### Fail-Safe Defaults
- Session cookies: HTTPONLY, SAMESITE by default
- CSRF protection: Enabled (blueprints exempted since they're JSON API)
- Rate limiting: In-memory tracking (configurable for production)
- Account lockout: Automatic after 5 failed attempts
- Password policy: Strict complexity requirements enforced at both validation layers

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

## Testing Patterns
- **Unit Tests**: Service classes tested in isolation (SecurityService, ValidationService)
- **Integration Tests**: End-to-end flows through routes with in-memory SQLite test DB
- **Fixtures**: `app` (Flask app with SQLite) and `client` (FlaskClient) in
  `tests/conftest.py`; each test gets a fresh DB via `db.drop_all()` teardown
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
