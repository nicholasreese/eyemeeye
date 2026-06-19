Installation
============

Prerequisites
-------------

- Python 3.11+
- Node.js 20+ and npm
- PostgreSQL (production) or SQLite (development/testing)

Backend Setup
-------------

.. code-block:: bash

   # Clone the repository
   git clone <repo-url>
   cd eyemeeye

   # Create and activate a virtual environment
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate

   # Install Python dependencies
   pip install -r requirements.txt

Frontend Setup
--------------

.. code-block:: bash

   cd src/frontend
   npm install

Database Setup
--------------

For local development the app creates a SQLite database automatically
on first run. For PostgreSQL, run the Alembic migrations:

.. code-block:: bash

   # Apply all migrations
   alembic upgrade head

   # Roll back one revision
   alembic downgrade -1

Running the Application
-----------------------

.. code-block:: bash

   # Backend (Flask dev server)
   python main.py

   # Frontend (Vite dev server with proxy to Flask)
   cd src/frontend && npm run dev

The Vite dev server at ``http://localhost:5173`` proxies all ``/api``
requests to Flask at ``http://localhost:5000``.

Running Tests
-------------

.. code-block:: bash

   make test              # run pytest with coverage
   make lint              # ruff lint check
   make format            # ruff format check
   make typecheck         # mypy strict check

Troubleshooting
---------------

**Import errors on startup**
   Ensure the virtual environment is active and ``pip install -r requirements.txt``
   has been run successfully.

**SQLite locked errors in tests**
   Tests use an in-memory SQLite database; each test session creates a
   fresh database so no manual cleanup is needed.

**Alembic "can't locate revision" error**
   Run ``alembic history`` to confirm the revision chain is intact.
   If the ``alembic_version`` table is missing, run ``alembic upgrade head``.
