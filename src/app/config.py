"""Application configuration dataclasses and helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class AppConfig:
    """Represents runtime configuration settings for the Flask app."""

    secret_key: str
    database_uri: str
    environment: str = "development"
    rate_limit: str = "100 per hour"
    enable_https: bool = False
    testing: bool = False
    mail_server: str = "localhost"
    mail_port: int = 587
    mail_use_tls: bool = True
    mail_username: str = ""
    mail_password: str = ""
    mail_sender: str = field(default="noreply@eyemeeye.com")

    def __post_init__(self) -> None:
        """Validates configuration values after initialization."""
        if not self.secret_key or len(self.secret_key) < 16:
            msg = "SECRET_KEY must be at least 16 characters long."
            raise ValueError(msg)
        if not self.database_uri:
            raise ValueError("DATABASE_URI must not be empty.")
        if not self.rate_limit:
            raise ValueError("RATE_LIMIT must be configured.")


def load_config() -> AppConfig:
    """Loads configuration values from environment variables."""

    secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    database_uri = os.getenv("DATABASE_URL", "sqlite:///app.db")
    environment = os.getenv("FLASK_ENV", "development")
    rate_limit = os.getenv("RATE_LIMIT", "100/hour")
    enable_https = os.getenv("ENABLE_HTTPS", "false").lower() == "true"
    testing = os.getenv("TESTING", "false").lower() == "true"
    mail_server = os.getenv("MAIL_SERVER", "localhost")
    mail_port = int(os.getenv("MAIL_PORT", "587"))
    mail_use_tls = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    mail_username = os.getenv("MAIL_USERNAME", "")
    mail_password = os.getenv("MAIL_PASSWORD", "")
    mail_sender = os.getenv("MAIL_SENDER", "noreply@eyemeeye.com")

    return AppConfig(
        secret_key=secret_key,
        database_uri=database_uri,
        environment=environment,
        rate_limit=rate_limit,
        enable_https=enable_https,
        testing=testing,
        mail_server=mail_server,
        mail_port=mail_port,
        mail_use_tls=mail_use_tls,
        mail_username=mail_username,
        mail_password=mail_password,
        mail_sender=mail_sender,
    )
