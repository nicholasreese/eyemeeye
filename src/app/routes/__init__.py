"""Registers application blueprints."""

from __future__ import annotations

from flask import Flask

from ..config import AppConfig
from ..extensions import csrf
from .auth import auth_bp
from .manager import manager_bp
from .user import user_bp


def register_blueprints(app: Flask, config: AppConfig) -> None:
    """Registers API blueprints with the Flask application."""

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(manager_bp, url_prefix="/api/manager")

    csrf.exempt(auth_bp)
    csrf.exempt(user_bp)
    csrf.exempt(manager_bp)
