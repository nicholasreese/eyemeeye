# Phone Management Application

## Overview
This web-based application allows users to manage their phone statuses, including options for online, sold, stolen, and disposed. The application follows best practices in object-oriented programming (OOP) and is built using Flask, React, and PostgreSQL.

## Project Structure
```
├── main.py
├── src/
│   ├── __init__.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── extensions.py
│   │   ├── models.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── manager.py
│   │   │   └── user.py
│   │   ├── services/
│   │   │   ├── auth.py
│   │   │   └── security.py
│   │   └── utils/
│   │       └── email.py
│   └── frontend/ (React application)
├── tests/
│   └── test_auth.py
├── docs/
│   ├── conf.py
│   └── index.rst
├── requirements.txt
├── pyproject.toml
├── Makefile
└── README.md
```

## Installation
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
make install
```

## Running the Backend
```bash
flask --app main run
```

## Running the Frontend
```bash
cd src/frontend
npm run dev
```

## Testing & Quality Checks
```bash
make format
make lint
make typecheck
make test
```

For an HTML coverage report:
```bash
make test-coverage
```

## Documentation
```bash
cd docs
make html
```

Or from project root:
```bash
make docs
```

## API Summary

Key backend modules and responsibilities:

- `app.models`: ORM models (`User`, `PhoneStatusHistory`, `AuditLog`).
- `app.services.security`: Password hashing, validation, TOTP helpers.
- `app.services.auth`: Registration, authentication, account lockout.
- `app.services.auditing`: Audit logging for security events.
- `app.services.validation`: Payload parsing and domain validation.
- `app.routes.*`: Flask Blueprints providing the API endpoints.

See the generated Sphinx docs for full API details.
