# Technical Context - Implementation Details

## Tech Stack
- **Language**: Python 3.11 (strict type checking); system Python 3.13 on dev macOS
- **Web Framework**: Flask 3.x with SQLAlchemy ORM
- **Frontend**: React 18 + TypeScript (Vite 5)
- **Database**: SQLite (development/testing), PostgreSQL (production)
- **Migrations**: Alembic 1.13 (two migrations: 001 initial schema, 002 OTP fields)
- **Security Libraries**: argon2-cffi, Flask-Talisman, Flask-WTF, Flask-Limiter
- **Email**: Flask-Mail (SMTP delivery; suppressed in tests via MAIL_SUPPRESS_SEND)
- **Testing**: pytest 8.2 + pytest-cov
- **Quality Tools**: ruff 0.4 (lint/format), mypy 1.10 (strict), bandit, pip-audit
- **Documentation**: Sphinx 7.3 (HTML output; intersphinx, napoleon, viewcode)
- **CI/CD**: GitHub Actions

## Key Dependencies (requirements.txt — sorted alphabetically)

### Production
```
alembic==1.13.1         # DB schema migrations
argon2-cffi==23.1.0     # Argon2 password hashing (passwords AND OTP codes)
Flask==3.0.2
Flask-Limiter==3.5.0    # Rate limiting (in-memory; Redis for prod)
Flask-Login==0.6.3
Flask-Mail==0.10.0      # SMTP email for verification + OTP delivery
Flask-SQLAlchemy==3.1.1
Flask-Talisman==1.1.0   # HTTPS/HSTS/CSP headers
Flask-WTF==1.2.1        # CSRF protection
psycopg[binary]==3.2.9  # PostgreSQL driver
pyotp==2.9.0            # TOTP secret generation (two_factor_secret still stored)
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
| `MAIL_SERVER` | `localhost` | SMTP host |
| `MAIL_PORT` | `587` | SMTP port |
| `MAIL_USE_TLS` | `true` | Enable STARTTLS |
| `MAIL_USERNAME` | `` | SMTP auth username |
| `MAIL_PASSWORD` | `` | SMTP auth password |
| `MAIL_SENDER` | `noreply@eyemeeye.com` | From address |

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
- two_factor_secret (base32, always generated — retained for possible future use)
- email_verification_token (nullable — cleared after verification)
- is_email_verified (bool, default false)
- **otp_code_hash** (nullable String 255 — Argon2 hash of pending email OTP)
- **otp_expires_at** (nullable DateTime — UTC expiry of the pending OTP)
- created_at

### phone_status_history
- id (PK), user_id (FK → users.id, CASCADE DELETE)
- status (enum: online/sold/stolen/disposed), noted_at

### audit_logs
- id (PK), event_type (string 64), username (nullable), message (text), created_at

### Alembic Migrations
- `001_initial_schema.py` — creates all three tables with enum types and FK cascade
- `002_add_email_otp_fields.py` — adds otp_code_hash + otp_expires_at to users

## API Surface

### /api/auth (CSRF-exempt)
- `POST /register` — username, email, phone_number, imei, password [, role]
  → 201; sends verification email via Flask-Mail
- `POST /login` — username, password
  → 202 + `{"requires_otp": true}` (validates password, checks email verified, sends OTP)
  → 403 if email not verified
  → 401 if credentials invalid
  → 429 if account locked
- `POST /verify-otp` — username, otp (6 digits)
  → 200 + session created (verifies OTP hash, clears OTP fields)
  → 401 if OTP invalid/expired
  → 429 if account locked
- `GET /verify-email?token=<tok>` — verifies email address
  → 200 on success, 400 on bad/missing token
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

### Authentication Flow
1. `POST /login` — validates password via Argon2; checks account lock status;
   checks `is_email_verified`; generates 6-digit OTP, hashes with Argon2, stores in
   `otp_code_hash`; sets `otp_expires_at` = now + 10 minutes; emails plaintext OTP
2. `POST /verify-otp` — checks account lock; finds user; validates expiry;
   verifies OTP hash (Argon2); clears OTP fields; clears failed login counter;
   calls `login_user(user)` to create Flask-Login session

### Password Policy
- Length: 8–128 characters
- Required character types: uppercase, lowercase, digit, special char from `@$!%*?&`
- Additional characters: any characters permitted (no whitelist restriction)
- Hash algorithm: Argon2id via argon2-cffi PasswordHasher defaults

### OTP Policy
- Length: 6 digits (zero-padded, `secrets.randbelow(1_000_000)`)
- Storage: Argon2 hash in `users.otp_code_hash` (plaintext never stored)
- Expiry: 10 minutes from generation (`users.otp_expires_at` UTC naive datetime)
- Delivery: Flask-Mail SMTP
- Failure tracking: same lockout counter as password failures

### Account Lockout
- Threshold: 5 consecutive failures (password failures + OTP failures combined)
- Tracking: `audit_logs` table (event_type = "failed_login")
- Reset: Successful full login (password + OTP) clears all failed_login entries
- Unlock: Admin must manually delete audit_log rows; no automatic expiry

### Rate Limiting
- Storage: In-memory (single process only)
- Default: 100 requests/hour per IP
- Production recommendation: Configure Redis storage backend

## Test Suite (99 tests, 10 modules)
| File | Tests | Coverage focus |
|---|---|---|
| test_auth.py | 14 | Registration, email verification, two-step login, OTP expiry/invalid, RBAC |
| test_config.py | 3 | AppConfig validation, env loading |
| test_email.py | 1 | `send_verification_email` calls `mail.send` with correct recipient |
| test_manager.py | 5 | Manager/admin endpoints |
| test_models.py | 4 | UserProfile, PhoneStatusRecord dataclasses |
| test_password_verification.py | 38 | Argon2 hash/verify, complexity rules, extended chars |
| test_responses.py | 2 | error_response, validation_error_response |
| test_security.py | 20 | Complexity validation, account lockout, audit logging |
| test_user.py | 3 | User profile, status update, status history |
| test_validation.py | 9 | Validators, RegisterData, LoginData, OtpData, UserUpdateData |

### Test Helper Pattern (email-OTP login)
All integration tests that log in follow this pattern:
```python
from unittest.mock import patch

# 1. Register
client.post("/api/auth/register", json={...})

# 2. Verify email (mandatory — login blocks without it)
with client.application.app_context():
    user = User.query.filter_by(username=username).one()
    token = user.email_verification_token
client.get(f"/api/auth/verify-email?token={token}")

# 3. Login step 1 — capture OTP via mock
with patch("src.app.services.auth.send_login_otp") as mock_send:
    client.post("/api/auth/login", json={"username": ..., "password": ...})
    # assert response.status_code == 202
    captured_otp = mock_send.call_args[0][1]  # second positional arg is plaintext OTP

# 4. Login step 2 — verify OTP
client.post("/api/auth/verify-otp", json={"username": ..., "otp": captured_otp})
# assert response.status_code == 200
```

## Known Issues / Technical Debt
- In-memory rate limiter: not suitable for multi-worker or multi-process production
- Account unlock: requires manual DB intervention, no admin endpoint or auto-expiry
- No password reset / account recovery flow
- Sphinx produces HTML only; PDF output requires LaTeX toolchain (not configured)
- venv in repo is Linux-built (x86_64 ELF); macOS requires system Python (3.13)
- `two_factor_secret` still stored per user (pyotp dep retained); not used in login
