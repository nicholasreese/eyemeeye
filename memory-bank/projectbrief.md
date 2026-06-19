# Phone Management Application - Project Brief

## Overview
A web-based application enabling users to manage phone lifecycle statuses
(online, sold, stolen, disposed) with role-based access control, security
auditing, and a React-based portal for user, manager, and admin workflows.

## Core Features

### User Management
- User registration with email verification token
- Secure authentication with optional two-factor authentication (TOTP)
- Role-based access control: USER, MANAGER, ADMIN
- Profile display (email, phone, IMEI, role)

### Phone Status Tracking
- Users update their phone status (online, sold, stolen, disposed)
- Complete status history with timestamps
- Manager/admin view access to all user statuses

### Administrative Interface
- Admin can view and manage all users
- Role promotion/demotion for users
- User detail editing (email, phone, IMEI)
- Audit trail of all administrative actions
- Admin edit form available in the React portal

### Security
- Password complexity enforcement (8–128 chars, mixed case, digits, special char)
- Any additional characters permitted in passwords (no whitelist restriction)
- Account lockout after 5 failed login attempts
- Security audit logging (login, role changes, unauthorized access)
- HTTPS support with secure session cookies
- CSRF protection and clickjacking prevention
- Security scanning in CI (bandit SAST, pip-audit)

## Technical Stack
- **Backend**: Python Flask 3.x with SQLAlchemy ORM
- **Frontend**: React 18 + TypeScript (Vite), single-page application
- **Database**: SQLite (dev/test), PostgreSQL (production via Alembic migrations)
- **Security**: Argon2 (password hashing), pyotp (2FA), Flask-Talisman, Flask-WTF
- **Migrations**: Alembic (schema management for PostgreSQL)
- **Testing**: pytest — 93 tests across 10 modules
- **Quality**: ruff (lint/format), mypy (strict type checking)
- **CI/CD**: GitHub Actions (backend + frontend jobs)
- **Docs**: Sphinx (installation, configuration, usage, API reference)

## Project Status (2026-06-18)
✅ Phase 1: User Authentication — Complete
✅ Phase 2: User Management — Complete
✅ Phase 3: Security & Best Practices — Complete
✅ Phase 4: Frontend + Documentation + CI — Complete

## Directory Layout
```
eyemeeye/
├── main.py                      # Flask entry point
├── alembic.ini                  # Alembic configuration
├── alembic/                     # Database migration scripts
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
├── src/
│   ├── app/
│   │   ├── __init__.py          # App factory
│   │   ├── config.py            # AppConfig dataclass
│   │   ├── extensions.py        # db, csrf, limiter, login_manager, talisman
│   │   ├── models.py            # User, PhoneStatusHistory, AuditLog ORM models
│   │   ├── routes/              # auth, user, manager blueprints + responses
│   │   ├── services/            # auth, security, auditing, user_management, validation
│   │   └── utils/               # email utility
│   └── frontend/
│       └── src/
│           ├── App.tsx          # React SPA (login, register, dashboard)
│           ├── App.css          # Styles including auth forms
│           ├── main.tsx         # Entry point
│           └── types.ts         # TypeScript interfaces
├── tests/                       # 10 test modules, 93 tests
├── docs/                        # Sphinx documentation source
├── .github/workflows/ci.yml     # GitHub Actions CI pipeline
├── Makefile                     # make install/test/lint/typecheck/security/migrate/ci
└── requirements.txt             # Python deps (incl. alembic, bandit, pip-audit)
```
