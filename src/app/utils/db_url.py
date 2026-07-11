"""Helpers for building safe database connection URLs."""

from __future__ import annotations

from urllib.parse import quote_plus, urlparse, urlunparse


def build_database_url(base_url: str, password: str = "") -> str:
    """Return a database URL with the psycopg v3 dialect prefix and a safely encoded password.

    Two transforms are applied in order:
    1. Rewrites bare ``postgresql://`` to ``postgresql+psycopg://`` (psycopg v3 requirement).
    2. If *password* is non-empty and the URL has no password component yet, injects it with
       ``quote_plus`` encoding so special characters (@, #, $, %, …) are safe in URLs.

    The result must never be passed to ``alembic_config.set_main_option`` because ConfigParser
    rejects ``%`` characters in values (interpolation syntax collision).  Pass it directly to
    ``create_engine`` or ``context.configure`` instead.
    """
    url = base_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if password and url.startswith("postgresql"):
        parsed = urlparse(url)
        if not parsed.password:
            netloc = (
                f"{parsed.username}:{quote_plus(password)}"
                f"@{parsed.hostname}:{parsed.port}"
            )
            url = urlunparse(parsed._replace(netloc=netloc))
    return url
