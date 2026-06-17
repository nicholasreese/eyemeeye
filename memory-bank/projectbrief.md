# Phone Management Application - Project Brief

## Overview
A web-based application enabling users to manage their phone lifecycle statuses (online, sold, stolen, disposed) with comprehensive role-based access control, security auditing, and administrative oversight.

## Core Features

### User Management
- User registration with email verification
- Secure authentication with two-factor authentication (TOTP)
- Role-based access control: USER, MANAGER, ADMIN
- Profile management (email, phone, IMEI)

### Phone Status Tracking
- Users update their phone status (online, sold, stolen, disposed)
- Complete status history with timestamps
- Manager/admin view access to user statuses

### Administrative Interface
- Admin can view and manage all users
- Role promotion/demotion for users
- User detail editing capabilities
- Audit trail of all administrative actions

### Security
- Password complexity enforcement (uppercase, lowercase, digit, special char, 8-128 chars)
- Account lockout after 5 failed login attempts
- Security audit logging (login, role changes, unauthorized access)
- HTTPS support with secure session cookies
- CSRF protection and click-jacking prevention

## Technical Stack
- **Backend**: Python Flask with SQLAlchemy ORM
- **Frontend**: React with TypeScript and Vite
- **Database**: SQLite (dev/test), PostgreSQL (production)
- **Security**: Argon2 (password hashing), pyotp (2FA), Flask-Talisman, Flask-WTF
- **Testing**: pytest with 89% code coverage
- **Quality**: ruff (lint/format), mypy (type checking)

## Project Status
✅ Phase 1: User Authentication - Complete
✅ Phase 2: User Management - Complete  
✅ Phase 3: Security & Best Practices - Complete
🔄 Phase 4: Testing, Documentation & Frontend - Next
