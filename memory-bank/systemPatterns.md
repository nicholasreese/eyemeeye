# System Architecture Patterns

## Layered Architecture

### 1. Routes Layer
- **Files**: `src/app/routes/{auth, user, manager}.py`
- **Responsibility**: HTTP request handling, input marshaling, response formatting
- **Pattern**: Flask Blueprints for modular endpoint organization
- **Security**: `@login_required` decorators, role checks via `auth_service.require_roles()`

### 2. Services Layer
- **Authentication Service** (`auth.py`)
  - User registration, login, password verification
  - TOTP verification, account lockout checking
  - Role-based authorization enforcement
  - Audit logging integration

- **Security Service** (`security.py`)
  - Password hashing (Argon2)
  - Password complexity validation
  - TOTP secret generation
  - Exception hierarchy: `HashingError`, `PasswordComplexityError`

- **Auditing Service** (`auditing.py`)
  - Security event logging (login, role changes, unauthorized access)
  - Failed login attempt tracking
  - Account lock event logging
  - Query capabilities for failed attempt counts

- **User Management Service** (`user_management.py`)
  - User listing and detail retrieval
  - User metadata updates
  - Phone status history querying

- **Validation Service** (`validation.py`)
  - Request payload parsing and validation
  - Domain-specific validators (email, phone, IMEI, password)
  - Whitelist-based field acceptance
  - Custom exception: `ValidationError`

### 3. Models Layer
- **ORM Models**: SQLAlchemy declarative base with relationships
  - `User`: User accounts with password hash, 2FA secret, email verification
  - `PhoneStatusHistory`: Immutable audit trail of status changes
  - `AuditLog`: Security event tracking

- **Domain Models**: Frozen dataclasses for validation
  - `RegisterData`, `LoginData`, `StatusUpdateData`, `RoleUpdateData`, `UserUpdateData`
  - Post-init validation with `ValidationError` exceptions

## Security Patterns

### Defense in Depth
1. **Input Validation**: Whitelist approach, type coercion, bounds checking
2. **Authentication**: Argon2 password hashing, TOTP-based 2FA
3. **Authorization**: Role-based access control enforced at service layer
4. **Auditing**: All sensitive operations logged with actor, resource, and action
5. **Communication**: HTTPS, HSTS, CSRF tokens, SameSite cookies (configurable)

### Fail-Safe Defaults
- Session cookies: HTTPONLY, SAMESITE by default
- CSRF protection: Enabled on all state-changing operations
- Rate limiting: In-memory tracking (configurable for production)
- Account lockout: Automatic after 5 failed attempts
- Password policy: Strict complexity requirements enforced

## Exception Hierarchy
```
Exception
├── ValidationError (input validation failures)
├── AuthError (authentication failures)
│   └── AccountLockedError (account lockout)
├── AuthorizationError (permission denied)
├── HashingError (password hashing failures)
├── PasswordComplexityError (password policy violations)
├── UserManagementError (user management failures)
│   └── UserNotFoundError (user lookup failures)
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
        # 4. Log significant events
        audit_service.log_event(...)
        # 5. Return formatted response
        return {"result": result}, 200
    except ValidationError as e:
        return validation_error_response(str(e))
    except AuthorizationError as e:
        audit_service.log_unauthorized_access(...)
        return error_response(str(e), 403)
```

## Data Flow Example: User Login
1. User sends credentials + TOTP token
2. Validation layer parses and validates input
3. Auth service checks for account lockout
4. Password hash verification
5. Audit logger records failed/successful attempt
6. On success: Clear failed attempts, set session, return 200
7. On failure: Log attempt, check lockout threshold, return 401 or 429

## Testing Patterns
- **Unit Tests**: Service classes with mocked dependencies
- **Integration Tests**: End-to-end flows through routes with test database
- **Fixtures**: Reusable test helpers for user registration, login, etc.
- **Coverage Goals**: 80%+ overall, 100% for critical security paths
