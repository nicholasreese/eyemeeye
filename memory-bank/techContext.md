# Technical Context - Implementation Details

## Tech Stack
- **Language**: Python 3.12 (strict type checking)
- **Web Framework**: Flask 2.x with SQLAlchemy ORM
- **Frontend**: React + TypeScript (Vite) - Phase 4
- **Database**: SQLite (development/testing), PostgreSQL (production)
- **Security Libraries**: argon2, pyotp, Flask-Talisman, Flask-WTF
- **Testing**: pytest with coverage plugins
- **Quality Tools**: ruff (lint/format), mypy (type checking)

## Key Dependencies

### Backend (requirements.txt)
```
Flask, Flask-SQLAlchemy, Flask-Login, Flask-Limiter
Flask-WTF (CSRF protection), Flask-Talisman (security headers)
argon2-cffi (password hashing), pyotp (TOTP), python-dotenv
pytest, pytest-cov, mypy, ruff
```

### Frontend (package.json) - Phase 4
```
React, React-Router, TypeScript, Axios
Tailwind CSS, Vite, ESLint, Prettier
```

## Environment Configuration

### Development (.env)
```
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-me
DATABASE_URL=sqlite:///app.db
ENABLE_HTTPS=false
RATE_LIMIT=100/hour
```

### Production (.env.prod)
```
FLASK_ENV=production
SECRET_KEY=<strong-random-32-char-key>
DATABASE_URL=postgresql://user:pass@localhost/db
ENABLE_HTTPS=true
RATE_LIMIT=100/hour
```

## Build & Deployment

### Local Development
```bash
make install          # Install all dependencies
make backend          # Install Python packages
make frontend         # Install Node packages
make test             # Run test suite (36 tests, 89% coverage)
make lint             # Run ruff linter
make typecheck        # Run mypy type checker
make format           # Auto-format with ruff
```

### Quality Gates
All commands must pass before code merge:
- `make test`: 36/36 tests passing
- `make lint`: No linting violations (ruff)
- `make typecheck`: No type errors (mypy strict)
- `make format`: Code formatted per ruff standards

## Database Schema

### Users Table
- id (PK), username (unique), email (unique), phone_number, imei
- password_hash, role (enum: USER/MANAGER/ADMIN)
- two_factor_secret, email_verification_token, is_email_verified
- created_at (timestamp)

### PhoneStatusHistory Table
- id (PK), user_id (FK), status (enum: ONLINE/SOLD/STOLEN/DISPOSED)
- noted_at (timestamp)

### AuditLog Table
- id (PK), event_type (string), username (nullable), message (text)
- created_at (timestamp)
- Indexes: (event_type, username), (created_at)

## API Endpoints

### Authentication (/api/auth)
- POST /register - User registration
- POST /login - User login with 2FA
- POST /logout - User logout

### User Management (/api/users)
- GET /me - Current user profile
- POST /status - Update phone status
- GET /status/options - Available status values
- GET /status/history - Status change history

### Manager/Admin (/api/manager)
- GET /users - List all users
- GET /users/<username> - User details + status history
- PATCH /users/<username> - Update user details (admin only)
- PATCH /users/<username>/role - Change user role (admin only)
- GET /users/<username>/statuses - User status history

## Security Configuration

### Session Management
- HTTPONLY: true (JavaScript cannot access cookies)
- SECURE: true if HTTPS enabled
- SAMESITE: Strict (default) / Lax
- Duration: Per Flask-Login default

### Password Policy
- Minimum 8 characters, maximum 128
- Must contain: uppercase, lowercase, digit, special char (@$!%*?&)
- Hashed with Argon2 (time cost: 2, memory cost: 65536 KB)

### Account Lockout Policy
- Max failed attempts: 5
- Lockout duration: Permanent until manual reset (admin)
- Tracking: In audit log with timestamps
- Bypass: Admin unlock or successful 2FA verification

### Rate Limiting
- Current: In-memory (development/testing)
- Production: Redis recommended
- Default: 100 requests per hour per IP
- Configurable via RATE_LIMIT env variable

## Monitoring & Logging

### Structured Logging
- Format: `%(asctime)s %(levelname)s %(name)s %(message)s`
- Output: stderr (via Flask WSGI)
- Levels: DEBUG (dev), INFO (prod)

### Security Events Logged
- Successful/failed login attempts (with reasons)
- Account lockouts
- Role changes (actor, target, old/new role)
- Unauthorized access attempts
- Failed 2FA attempts

### Audit Trail
- All events: user, action, timestamp, message
- Retention: Indefinite (production should set policy)
- Access: Admin dashboard (Phase 4)
- Queries: Failed login count, role change history

## Known Issues & Planned Improvements

### Current Warnings
⚠️ SQLAlchemy deprecation: Query.get() → Session.get() (Phase 4)
⚠️ In-memory rate limiter: Configure Redis for production
⚠️ Account unlock: Requires admin intervention (automate? Phase 4)

### Phase 4 Deliverables
- Frontend React dashboard with TypeScript
- Admin panel for user/role management
- User self-service profile editing
- Audit log viewer for admins
- Email verification flow UI
- Sphinx documentation site
- CI/CD pipeline (GitHub Actions)
- Security scanning (bandit, pip-audit)
- Performance monitoring
- Database migration tools (Alembic)
