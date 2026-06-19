# EyeMeEye — Stop Mobile Phone Theft

A secure, role-based web application for tracking phone lifecycle status
(online, sold, stolen, disposed). Built with Flask, React, and PostgreSQL.

---

## Project Structure

```text
eyemeeye/
├── main.py                        # Flask entry point
├── Dockerfile                     # Backend image (Flask + gunicorn)
├── docker-compose.yml             # Full-stack deployment
├── nginx/
│   ├── Dockerfile                 # Frontend image (React build → nginx)
│   └── nginx.conf                 # nginx reverse-proxy config
├── alembic.ini                    # Alembic migration config
├── alembic/                       # Database migration scripts
├── src/
│   ├── app/                       # Flask application
│   │   ├── config.py              # AppConfig (env var loading)
│   │   ├── extensions.py          # db, csrf, limiter, login_manager, talisman
│   │   ├── models.py              # User, PhoneStatusHistory, AuditLog ORM models
│   │   ├── routes/                # auth, user, manager blueprints
│   │   ├── services/              # auth, security, auditing, validation, user_management
│   │   └── utils/                 # email utility
│   └── frontend/                  # React + TypeScript (Vite)
│       └── src/
│           ├── App.tsx            # SPA — login, register, dashboard
│           └── types.ts           # TypeScript interfaces
├── tests/                         # pytest — 93 tests across 10 modules
├── docs/                          # Sphinx documentation source
├── .github/workflows/ci.yml       # GitHub Actions CI
├── Makefile                       # Developer shortcuts
└── requirements.txt               # Python dependencies
```

---

## Docker Compose Deployment

This is the recommended way to run EyeMeEye in production. Three containers are
orchestrated:

| Service | Image | Role |
| --- | --- | --- |
| `db` | `postgres:16-alpine` | PostgreSQL database with persistent volume |
| `api` | Built from `Dockerfile` | Flask app served by gunicorn (4 workers) |
| `web` | Built from `nginx/Dockerfile` | React SPA + reverse proxy to `api` |

### Prerequisites

- [Docker Engine](https://docs.docker.com/engine/install/) 24+
- [Docker Compose](https://docs.docker.com/compose/install/) v2 (bundled with Docker Desktop)

Verify both are available:

```bash
docker --version
docker compose version
```

### 1. Clone the repository

```bash
git clone <your-repo-url> eyemeeye
cd eyemeeye
```

### 2. Create your environment file

```bash
cp .env.example .env
```

Open `.env` and set real values for the two required secrets:

```env
# Must be at least 16 characters — use a random string
SECRET_KEY=replace-with-a-random-32-character-string

# PostgreSQL password — choose a strong password
POSTGRES_PASSWORD=replace-with-a-strong-password

# Optional
RATE_LIMIT=100/hour
ENABLE_HTTPS=false
PORT=80
```

> **Security**: Never commit `.env` to version control. The `.gitignore` already
> excludes `.env` files. Generate a strong `SECRET_KEY` with:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Build and start all services

```bash
docker compose up --build -d
```

This will:

1. Pull the `postgres:16-alpine` base image
2. Build the Flask backend image (installs Python deps + gunicorn)
3. Build the nginx image (compiles the React app, then copies the static output into nginx)
4. Start `db` first and wait until PostgreSQL is healthy
5. Run `alembic upgrade head` to apply all database migrations
6. Start gunicorn with 4 workers
7. Start nginx on port 80 (or `PORT` from `.env`)

The app will be available at **<http://localhost>** (or your server's IP/domain).

### 4. Verify the deployment

```bash
# Check all three containers are running
docker compose ps

# Tail live logs from all services
docker compose logs -f

# Test the API health via the login endpoint
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"nonexistent","password":"test"}'
# Expected: {"message": "Invalid credentials."}
```

---

## Managing the Deployment

### View logs

```bash
# All services
docker compose logs -f

# Individual service
docker compose logs -f api
docker compose logs -f web
docker compose logs -f db
```

### Stop and restart

```bash
# Stop all containers (data is preserved in the postgres_data volume)
docker compose down

# Stop and remove the database volume (DELETES ALL DATA)
docker compose down -v

# Restart a single service after a code change
docker compose up --build -d api
```

### Apply database migrations

Migrations run automatically on `api` container start. To run them manually:

```bash
docker compose exec api alembic upgrade head
```

To check the current migration revision:

```bash
docker compose exec api alembic current
```

### Open a database shell

```bash
docker compose exec db psql -U eyemeeye -d eyemeeye
```

### Run a one-off command in the backend container

```bash
# Open a shell
docker compose exec api sh

# Run the test suite against the production database (use with caution)
docker compose exec api python -m pytest
```

### Scale API workers

To run multiple API container replicas behind the nginx proxy, update
`docker-compose.yml` to remove the fixed port binding from `api` and then:

```bash
docker compose up --scale api=3 -d
```

---

## Backup and Restore

### Backup the database

```bash
docker compose exec db pg_dump -U eyemeeye eyemeeye > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore from a backup

```bash
# Stop the api service to avoid writes during restore
docker compose stop api

cat backup_20260620_120000.sql | docker compose exec -T db psql -U eyemeeye -d eyemeeye

docker compose start api
```

---

## Production Checklist

- [ ] `SECRET_KEY` is at least 32 random characters and not committed to git
- [ ] `POSTGRES_PASSWORD` is strong and not reused elsewhere
- [ ] `ENABLE_HTTPS=true` and TLS termination is configured (nginx or reverse proxy)
- [ ] Port 5000 (Flask) is **not** exposed directly; all traffic goes through nginx on port 80/443
- [ ] `docker compose logs` shows no errors after startup
- [ ] `alembic upgrade head` completed successfully (check `api` logs)
- [ ] Database volume is included in your backup schedule

---

## Local Development (without Docker)

### Backend

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
make install

# macOS: port 5000 is taken by AirPlay — use 5001
SECRET_KEY="dev-secret-key-for-testing" DATABASE_URL="sqlite:///app.db" python main.py --port 5001
```

### Frontend

```bash
cd src/frontend
npm install
npm run dev     # Vite dev server at http://localhost:5173 (proxies /api → :5001)
```

### Testing & Quality Checks

```bash
make format       # Auto-format with ruff
make lint         # Lint check
make typecheck    # mypy strict
make test         # pytest with coverage
make security     # bandit SAST + pip-audit CVE scan
make ci           # Run all of the above in sequence
```

For an HTML coverage report:

```bash
make test-coverage
```

### Database migrations (local)

```bash
# Apply all pending migrations
make migrate

# Or directly:
alembic upgrade head
```

---

## Documentation

```bash
make docs
# Output: docs/_build/html/index.html
```

---

## API Summary

| Prefix | Auth required | Description |
| --- | --- | --- |
| `POST /api/auth/register` | No | Create a new user account |
| `POST /api/auth/login` | No | Log in (optional TOTP token) |
| `POST /api/auth/logout` | Yes | End the session |
| `GET /api/users/me` | Yes | Current user profile |
| `POST /api/users/status` | Yes | Update phone status |
| `GET /api/users/status/history` | Yes | Status history |
| `GET /api/manager/users` | Manager/Admin | List all users |
| `GET /api/manager/users/<username>` | Manager/Admin | User detail + history |
| `PATCH /api/manager/users/<username>` | Admin | Edit user fields or role |

See `docs/usage.rst` or the generated Sphinx docs for full request/response details.
