Configuration
=============

All runtime settings are loaded from environment variables (or a ``.env``
file in the project root via ``python-dotenv``).

Environment Variables
---------------------

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Variable
     - Default
     - Description
   * - ``SECRET_KEY``
     - ``dev-secret-key-change-me``
     - Flask secret key used for session signing. **Must be changed**
       in production. Minimum 16 characters.
   * - ``DATABASE_URL``
     - ``sqlite:///app.db``
     - SQLAlchemy connection string. Use a ``postgresql://`` URL in
       production.
   * - ``FLASK_ENV``
     - ``development``
     - Runtime environment. Set to ``production`` to reduce log
       verbosity.
   * - ``RATE_LIMIT``
     - ``100/hour``
     - Global rate limit applied to all endpoints via Flask-Limiter.
   * - ``ENABLE_HTTPS``
     - ``false``
     - When ``true``, enables HSTS, secure cookies, and forces HTTPS
       redirects via Flask-Talisman.
   * - ``TESTING``
     - ``false``
     - Enables Flask testing mode (disables error catching, etc.).

Example ``.env`` File
---------------------

.. code-block:: bash

   SECRET_KEY=change-me-to-a-long-random-string
   DATABASE_URL=postgresql://user:pass@localhost:5432/eyemeeye
   FLASK_ENV=production
   RATE_LIMIT=200/hour
   ENABLE_HTTPS=true

.. warning::

   Never commit ``.env`` files containing real secrets to version
   control. The project ``.gitignore`` already excludes ``.env``.

Account Lockout Policy
----------------------

Accounts are locked after **5 consecutive failed login attempts**.
The lockout count is tracked in the ``audit_logs`` table. An admin
must manually clear the failed-login entries to unlock an account.

Password Policy
---------------

Passwords must meet all of the following requirements:

- 8–128 characters in length
- At least one uppercase letter (``A–Z``)
- At least one lowercase letter (``a–z``)
- At least one digit (``0–9``)
- At least one special character from ``@$!%*?&``
