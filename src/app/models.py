"""Domain dataclasses and SQLAlchemy models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

from flask_login import UserMixin
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import validates

from .extensions import db

if TYPE_CHECKING:

    class _BaseModel:
        """Typed base model used exclusively for static analysis."""

        query: Any
        __tablename__: ClassVar[str]
        id: int

    class _UserMixin:
        """Typed representation of the Flask-Login user mixin."""

        is_authenticated: bool
        is_active: bool
        is_anonymous: bool
        get_id: Any

else:  # pragma: no cover - runtime assignment for SQLAlchemy
    _BaseModel = db.Model
    _UserMixin = UserMixin


class Role(str, Enum):
    """Represents the access level of a system user."""

    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class PhoneStatus(str, Enum):
    """Enumerates the permitted phone lifecycle statuses."""

    ONLINE = "online"
    SOLD = "sold"
    STOLEN = "stolen"
    DISPOSED = "disposed"


@dataclass
class UserProfile:
    """Dataclass representing validated user metadata."""

    username: str
    email: str
    phone_number: str
    imei: str
    role: Role = Role.USER

    def __post_init__(self) -> None:
        """Validates user profile data."""

        if len(self.username) < 3:
            msg = "Username must be at least 3 characters long."
            raise ValueError(msg)
        if "@" not in self.email:
            raise ValueError("Email address must contain '@'.")
        if not self.phone_number.isdigit() or len(self.phone_number) < 10:
            raise ValueError("Phone number must be numeric with 10+ digits.")
        if len(self.imei) not in {14, 15}:
            raise ValueError("IMEI must be 14 or 15 digits long.")


@dataclass
class PhoneStatusRecord:
    """Dataclass capturing a phone status entry for auditing."""

    username: str
    status: PhoneStatus
    noted_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))

    def __post_init__(self) -> None:
        """Validates the phone status record."""

        if not self.username:
            raise ValueError("username is required for status tracking.")


class User(_UserMixin, _BaseModel):
    """Persistent database representation of a user."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    imei = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(SAEnum(Role), default=Role.USER, nullable=False)
    two_factor_secret = db.Column(db.String(32), nullable=True)
    email_verification_token = db.Column(db.String(64), nullable=True)
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    statuses = db.relationship(
        "PhoneStatusHistory",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    @validates("username")
    def validate_username(self, _key: str, username: str) -> str:
        """Ensures usernames adhere to the defined constraints."""

        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        return username


class PhoneStatusHistory(_BaseModel):
    """Historical phone status entries per user."""

    __tablename__ = "phone_status_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(SAEnum(PhoneStatus), nullable=False)
    noted_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )


class AuditLog(_BaseModel):
    """Audit trail tracking important business events."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(64), nullable=False)
    username = db.Column(db.String(80), nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )
