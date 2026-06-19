Phone Management Application
============================

A secure, role-based web application for tracking phone lifecycle
statuses (online, sold, stolen, disposed) with full audit logging,
two-factor authentication, and a React portal.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   configuration
   usage

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api

Overview
--------

**Roles**

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - Role
     - Capabilities
   * - ``user``
     - Register, log in, update personal phone status, view own history
   * - ``manager``
     - Read-only access to all users and their status histories
   * - ``admin``
     - Full access: edit user details, promote/demote roles, view audit logs

**Phone Statuses**

``online`` · ``sold`` · ``stolen`` · ``disposed``

**Security Highlights**

- Argon2 password hashing
- TOTP-based two-factor authentication (pyotp)
- Account lockout after 5 failed login attempts
- CSRF protection on all state-changing endpoints
- HTTPS/HSTS support via Flask-Talisman
- Comprehensive security audit log

Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
