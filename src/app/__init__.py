"""Application factory for the phone management backend."""

from __future__ import annotations

import logging
from logging.config import dictConfig

from flask import Flask

from .config import AppConfig, load_config
from .extensions import csrf, db, limiter, login_manager, talisman
from .routes import register_blueprints
from .services.auth import AuthService


def _configure_logging(app: Flask) -> None:
    """Configures structured logging for the Flask application."""

    log_level = logging.DEBUG if app.config["ENV"] == "development" else logging.INFO
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://flask.logging.wsgi_errors_stream",
                    "formatter": "default",
                }
            },
            "root": {
                "level": log_level,
                "handlers": ["wsgi"],
            },
        }
    )


def create_app(config: AppConfig | None = None) -> Flask:
    """Creates and configures the Flask application."""

    app_config = config or load_config()
    app = Flask(__name__, static_folder="../frontend/public")
    app.config.update(
        SECRET_KEY=app_config.secret_key,
        SQLALCHEMY_DATABASE_URI=app_config.database_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        ENV=app_config.environment,
        TESTING=app_config.testing,
    )

    if app_config.enable_https:
        app.config.update(
            SESSION_COOKIE_SECURE=True,
            REMEMBER_COOKIE_SECURE=True,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE="Strict",
            PREFERRED_URL_SCHEME="https",
        )
    else:
        app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
        app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    talisman.init_app(
        app,
        force_https=app_config.enable_https,
        strict_transport_security=app_config.enable_https,
        session_cookie_secure=app_config.enable_https,
    )
    login_manager.init_app(app)

    _configure_logging(app)

    with app.app_context():
        db.create_all()

    @login_manager.unauthorized_handler
    def _unauthorized() -> tuple[dict[str, str], int]:
        return {"message": "Authentication required."}, 401

    login_manager.user_loader(AuthService.load_user_by_id)

    register_blueprints(app, app_config)

    return app
