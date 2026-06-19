# Technical Context - Implementation Details

## Tech Stack
- **Language**: Python 3.11 (strict type checking); system Python 3.13 on dev macOS
- **Web Framework**: Flask 3.x with SQLAlchemy ORM
- **Frontend**: React 18 + TypeScript (Vite 5)
- **Database**: SQLite (development/testing), PostgreSQL (production)
- **Migrations**: Alembic 1.13
- **Security Libraries**: argon2-cffi, pyotp, Flask-Talisman, Flask-WTF, Flask-Limiter
- **Testing**: pytest 8.2 + pytest-cov
- **Quality Tools**: ruff 0.4 (lint/format), mypy 1.10 (strict), bandit, pip-audit
- **Documentation**: Sphinx 7.3 (HTML output; intersphinx, napoleon, viewcode)
- **CI/CD**: GitHub Actions

## Key Dependencies (requirements.txt — sorted alphabetically)

### Production
```
alembic==1.13.1         # DB schema migrations
argon2-cffi==23.1.0     # Argon2 password hashing
Flask==3.0.2
Flask-Limiter==3.5.0    # Rate limiting (in-memory; Redis for prod)
Flask-Login==0.6.3
Flask-SQLAlchemy==3.1.1
Flask-Talisman==1.1.0   # HTTPS/HSTS/CSP headers
Flask-WTF==1.2.1        # CSRF protection
psycopg[binary]==3.2.9  # PostgreSQL driver
pyotp==2.9.0            # TOTP two-factor auth
python-dotenv==1.0.1
```

### Development & Tooling
```
bandit==1.7.9           # SAST security scanner
mypy==1.10.0
pip-audit==2.7.3        # Dependency CVE scanner
pytest==8.2.2
pytest-cov==5.0.0
ruff==0.4.4
Sphinx==7.3.7
```

### Frontend (package.json)
```
react@18.3.1, react-dom@18.3.1
typescript@5.4.5, vite@5.2.12, @vitejs/plugin-react@4.3.1
```

## Environment Configuration

### Required Environment Variables
| Variable | Default | Notes |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key-change-me` | Min 16 chars. **Must change for prod.** |
| `DATABASE_URL` | `sqlite:///app.db` | Use `postgresql://` URL in prod |
| `FLASK_ENV` | `development` | Set `production` to reduce log noise |
| `RATE_LIMIT` | `100/hour` | Flask-Limiter rate limit string |
| `ENABLE_HTTPS` | `false` | `true` enables HSTS + secure cookies |
| `TESTING` | `false` | Flask testing mode |

### Local Dev Note
The `.env` file ships with `SECRET_KEY=your_secret_key` (15 chars — below the 16-char
minimum). Override via env var when starting Flask:
```bash
SECRET_KEY="dev-secret-key-for-testing" DATABASE_URL="sqlite:///app.db" python main.py
```

### macOS Port Conflict
Port 5000 is occupied by AirPlay Receiver on macOS Ventura+. Run Flask on 5001:
```bash
flask run --port 5001
```
`src/frontend/vite.config.ts` proxies `/api` → `http://localhost:5001`.

## Makefile Targets
```
make install          Install all dependencies (backend + frontend)
make backend          pip install -r requirements.txt
make frontend         cd src/frontend && npm install
make lint             ruff check
make format           ruff format
make typecheck        mypy src
make test             pytest --cov=src --cov-report=term-missing
make test-coverage    pytest with HTML coverage report
make security         bandit -r src/ + pip_audit
make migrate          alembic upgrade head
make docs             cd docs && make html
make ci               lint + format + typecheck + test + security (all CI checks)
```

## Database Schema

### users
- id (PK), username (unique, 3–80 chars), email (unique), phone_number, imei
- password_hash (Argon2), role (enum: user/manager/admin, default user)
- two_factor_secret (base32, always generated), email_verification_token
- is_email_verified (bool, default false), created_at

### phone_status_history
- id (PK), user_id (FK → users.id, CASCADE DELETE)
- status (enum: online/sold/stolen/disposed), noted_at

### audit_logs
- id (PK), event_type (string 64), username (nullable), message (text), created_at

## API Surface

### /api/auth (CSRF-exempt)
- `POST /register` — username, email, phone_number, imei, password [, role]
- `POST /login` — username, password [, token (6-digit TOTP)]
- `POST /logout` — requires authentication

### /api/users (CSRF-exempt, login required)
- `GET /me` — current user profile JSON
- `POST /status` — { status: "online"|"sold"|"stolen"|"disposed" }
- `GET /status/options` — list of valid status values
- `GET /status/history` — chronological status entries

### /api/manager (CSRF-exempt, login required, manager/admin role)
- `GET /users` — list all users
- `GET /users/<username>` — user + status history
- `PATCH /users/<username>` — update email/phone/imei/role (admin only)
- `PATCH /users/<username>/role` — role change (admin only)
- `GET /users/<username>/statuses` — status history for a specific user

## Security Configuration

### Session Management
- HTTPONLY: always true
- SECURE: true when ENABLE_HTTPS=true
- SAMESITE: Strict (HTTPS) / Lax (HTTP)

### Password Policy
- Length: 8–128 characters
- Required character types: uppercase, lowercase, digit, special char from `@$!%*?&`
- Additional characters: any characters permitted (no whitelist restriction)
- Hash algorithm: Argon2id via argon2-cffi PasswordHasher defaults

### Account Lockout
- Threshold: 5 consecutive failed logins
- Tracking: `audit_logs` table (event_type = "failed_login")
- Reset: Successful login clears all failed_login entries for that username
- Unlock: Admin must manually delete audit_log rows or there is no automatic expiry

### Rate Limiting
- Storage: In-memory (single process only)
- Default: 100 requests/hour per IP
- Production recommendation: Configure Redis storage backend

## Test Suite (93 tests, 10 modules)
| File | Tests | Coverage focus |
|---|---|---|
| test_auth.py | 8 | Registration, login, logout, TOTP, RBAC |
| test_config.py | 3 | AppConfig validation, env loading |
| test_email.py | 1 | Email utility logging |
| test_manager.py | 5 | Manager/admin endpoints |
| test_models.py | 4 | UserProfile, PhoneStatusRecord dataclasses |
| test_password_verification.py | 38 | Argon2 hash/verify, complexity rules, extended chars |
| test_responses.py | 2 | error_response, validation_error_response |
| test_security.py | 20 | Complexity validation, account lockout, audit logging |
| test_user.py | 3 | User profile, status update, status history |
| test_validation.py | 9 | Validators, RegisterData, LoginData, UserUpdateData |

## Known Issues / Technical Debt
- In-memory rate limiter: not suitable for multi-worker or multi-process production
- Email sending is a stub: logs intent but does not deliver email
- No email verification enforcement: users can log in without verifying email
- 2FA is optional per-login: no per-user "enforce 2FA" flag
- Account unlock: requires manual DB intervention, no admin endpoint
- No password reset / account recovery flow
- Sphinx produces HTML only; PDF output requires LaTeX toolchain (not configured)
- venv in repo is Linux-built (x86_64 ELF); macOS requires system Python (3.13)
