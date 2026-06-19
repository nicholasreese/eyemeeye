Usage Guide
===========

REST API
--------

All endpoints are prefixed with ``/api``. The API uses JSON for both
request bodies and responses. Authentication is session-based (cookie).

Authentication Endpoints
~~~~~~~~~~~~~~~~~~~~~~~~

**Register a new user**

.. code-block:: http

   POST /api/auth/register
   Content-Type: application/json

   {
     "username": "alice",
     "email": "alice@example.com",
     "phone_number": "5551234567",
     "imei": "123456789012345",
     "password": "S3cur3P@ss!"
   }

Response (201 Created):

.. code-block:: json

   { "message": "User alice registered." }

**Log in**

.. code-block:: http

   POST /api/auth/login
   Content-Type: application/json

   {
     "username": "alice",
     "password": "S3cur3P@ss!",
     "token": "123456"
   }

``token`` is optional and only required when 2FA is configured.

Response (200 OK):

.. code-block:: json

   { "message": "Login successful." }

**Log out**

.. code-block:: http

   POST /api/auth/logout

User Endpoints (authenticated)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Get current user profile**

.. code-block:: http

   GET /api/users/me

**Update phone status**

.. code-block:: http

   POST /api/users/status
   Content-Type: application/json

   { "status": "sold" }

Valid values: ``online``, ``sold``, ``stolen``, ``disposed``.

**Get status history**

.. code-block:: http

   GET /api/users/status/history

**Get allowed status values**

.. code-block:: http

   GET /api/users/status/options

Manager / Admin Endpoints
~~~~~~~~~~~~~~~~~~~~~~~~~

Require ``manager`` or ``admin`` role.

**List all users**

.. code-block:: http

   GET /api/manager/users

**Get user details with status history**

.. code-block:: http

   GET /api/manager/users/{username}

**Update user details** (admin only)

.. code-block:: http

   PATCH /api/manager/users/{username}
   Content-Type: application/json

   {
     "email": "new@example.com",
     "phone_number": "5559876543",
     "imei": "987654321012345",
     "role": "manager"
   }

All fields are optional; include only what needs to change.

**Update user role** (admin only)

.. code-block:: http

   PATCH /api/manager/users/{username}/role
   Content-Type: application/json

   { "role": "manager" }

Error Responses
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 10 90

   * - Status
     - Meaning
   * - 400
     - Validation error — response body contains a ``message`` field
   * - 401
     - Authentication required or credentials invalid
   * - 403
     - Insufficient role permissions
   * - 404
     - Resource not found
   * - 429
     - Account locked (too many failed login attempts)

React Portal
------------

The frontend SPA at ``/`` provides a full UI for all workflows:

- **Login / Register** — session-aware; redirects to dashboard on success
- **Dashboard** — displays profile, status update form, and status history
- **Manager view** — visible to ``manager`` and ``admin`` roles; lists all
  users and shows details on selection
- **Admin edit form** — shown inside the manager panel for ``admin`` users;
  edits email, phone, IMEI, and role inline

Two-Factor Authentication
--------------------------

After registration, a TOTP secret is generated and stored. Retrieve the
provisioning URI via the ``pyotp`` library and scan it with an
authenticator app (Google Authenticator, Authy, etc.):

.. code-block:: python

   import pyotp

   totp = pyotp.TOTP(user.two_factor_secret)
   print(totp.provisioning_uri(user.email, issuer_name="EyeMeEye"))

Pass the 6-digit code as ``"token"`` in the login request body.
