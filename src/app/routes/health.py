"""Health check endpoint for load balancer and uptime monitoring."""

from __future__ import annotations

from flask import Blueprint

from ..extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health() -> tuple[dict[str, object], int]:
    """Returns 200 when the app and database connection are healthy."""

    try:
        db.session.execute(db.text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    if db_ok:
        return {"status": "ok"}, 200
    return {"status": "degraded", "detail": "database unreachable"}, 503
