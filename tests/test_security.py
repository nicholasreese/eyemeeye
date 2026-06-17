"""Security and input validation tests for Phase 3."""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.app.models import User
from src.app.services.security import PasswordComplexityError, SecurityService


class TestPasswordComplexityValidation:
    """Tests for password complexity requirements."""

    def test_password_missing_uppercase(self) -> None:
        """Password without uppercase letter should fail."""
        service = SecurityService()
        with pytest.raises(PasswordComplexityError):
            service.validate_password_complexity("password1@test")

    def test_password_missing_lowercase(self) -> None:
        """Password without lowercase letter should fail."""
        service = SecurityService()
        with pytest.raises(PasswordComplexityError):
            service.validate_password_complexity("PASSWORD1@TEST")

    def test_password_missing_digit(self) -> None:
        """Password without digit should fail."""
        service = SecurityService()
        with pytest.raises(PasswordComplexityError):
            service.validate_password_complexity("PasswordTest@")

    def test_password_missing_special_char(self) -> None:
        """Password without special character should fail."""
        service = SecurityService()
        with pytest.raises(PasswordComplexityError):
            service.validate_password_complexity("Password1Test")

    def test_password_too_short(self) -> None:
        """Password less than 8 characters should fail."""
        service = SecurityService()
        with pytest.raises(PasswordComplexityError):
            service.validate_password_complexity("Pass1@")

    def test_password_too_long(self) -> None:
        """Password exceeding 128 characters should fail."""
        service = SecurityService()
        long_password = "A" * 120 + "a1@" + "x" * 10
        with pytest.raises(PasswordComplexityError):
            service.validate_password_complexity(long_password)

    def test_valid_password(self) -> None:
        """Valid password should pass validation."""
        service = SecurityService()
        service.validate_password_complexity("ValidPass1@word")

    def test_valid_password_with_multiple_special_chars(self) -> None:
        """Password with multiple special characters should be valid."""
        service = SecurityService()
        service.validate_password_complexity("Valid$Pass1@word!")


class TestInputValidationEnhancements:
    """Tests for enhanced input validation."""

    def test_register_with_weak_password(self, client: FlaskClient) -> None:
        """Registration with weak password should fail."""
        response: TestResponse = client.post(
            "/api/auth/register",
            json={
                "username": "weakpass",
                "email": "weakpass@example.com",
                "phone_number": "1234567890",
                "imei": "12345678901234",
                "password": "weak",
            },
        )
        assert response.status_code == 400
        payload = response.get_json()
        assert "password" in payload["message"].lower()

    def test_register_with_password_missing_uppercase(
        self, client: FlaskClient
    ) -> None:
        """Registration with password lacking uppercase should fail."""
        response: TestResponse = client.post(
            "/api/auth/register",
            json={
                "username": "noupper",
                "email": "noupper@example.com",
                "phone_number": "1234567890",
                "imei": "12345678901234",
                "password": "password1@test",
            },
        )
        assert response.status_code == 400
        payload = response.get_json()
        assert "uppercase" in payload["message"].lower()

    def test_register_with_password_missing_special_char(
        self, client: FlaskClient
    ) -> None:
        """Registration with password lacking special character should fail."""
        response: TestResponse = client.post(
            "/api/auth/register",
            json={
                "username": "nospecial",
                "email": "nospecial@example.com",
                "phone_number": "1234567890",
                "imei": "12345678901234",
                "password": "Password1Test",
            },
        )
        assert response.status_code == 400
        payload = response.get_json()
        assert "special" in payload["message"].lower()

    def test_register_with_valid_complex_password(self, client: FlaskClient) -> None:
        """Registration with valid complex password should succeed."""
        response: TestResponse = client.post(
            "/api/auth/register",
            json={
                "username": "validpass",
                "email": "validpass@example.com",
                "phone_number": "1234567890",
                "imei": "12345678901234",
                "password": "ValidPass@123",
            },
        )
        assert response.status_code == 201

    def test_register_with_username_too_short(self, client: FlaskClient) -> None:
        """Username shorter than 3 characters should fail."""
        response: TestResponse = client.post(
            "/api/auth/register",
            json={
                "username": "ab",
                "email": "short@example.com",
                "phone_number": "1234567890",
                "imei": "12345678901234",
                "password": "ValidPass@123",
            },
        )
        assert response.status_code == 400
        payload = response.get_json()
        assert "username" in payload["message"].lower()

    def test_register_with_username_too_long(self, client: FlaskClient) -> None:
        """Username exceeding 80 characters should fail."""
        long_username = "a" * 81
        response: TestResponse = client.post(
            "/api/auth/register",
            json={
                "username": long_username,
                "email": "long@example.com",
                "phone_number": "1234567890",
                "imei": "12345678901234",
                "password": "ValidPass@123",
            },
        )
        assert response.status_code == 400


class TestAccountLockout:
    """Tests for account lockout after failed login attempts."""

    def test_account_locks_after_failed_attempts(self, client: FlaskClient) -> None:
        """Account should lock after 5 failed login attempts."""
        response: TestResponse = client.post(
            "/api/auth/register",
            json={
                "username": "locktest",
                "email": "locktest@example.com",
                "phone_number": "1234567890",
                "imei": "12345678901234",
                "password": "ValidPass@123",
            },
        )
        assert response.status_code == 201

        for i in range(5):
            response = client.post(
                "/api/auth/login",
                json={"username": "locktest", "password": "WrongPass@123"},
            )
            if i < 4:
                assert response.status_code == 401
            else:
                assert response.status_code in {401, 429}

        response = client.post(
            "/api/auth/login",
            json={"username": "locktest", "password": "ValidPass@123"},
        )
        assert response.status_code == 429
        payload = response.get_json()
        assert "locked" in payload["message"].lower()

    def test_failed_login_attempt_logged(self, client: FlaskClient) -> None:
        """Failed login attempts should be logged in audit trail."""
        response: TestResponse = client.post(
            "/api/auth/register",
            json={
                "username": "audituser",
                "email": "audituser@example.com",
                "phone_number": "1234567890",
                "imei": "12345678901234",
                "password": "ValidPass@123",
            },
        )
        assert response.status_code == 201

        response = client.post(
            "/api/auth/login",
            json={"username": "audituser", "password": "WrongPass@123"},
        )
        assert response.status_code == 401

        with client.application.app_context():
            from src.app.models import AuditLog

            logs = (
                AuditLog.query.filter_by(
                    event_type="failed_login", username="audituser"
                )
                .order_by(AuditLog.created_at.desc())
                .all()
            )
            assert len(logs) > 0
            assert "Invalid password" in logs[0].message

    def test_successful_login_clears_failed_attempts(self, client: FlaskClient) -> None:
        """Successful login should clear failed attempt tracking."""
        import pyotp

        response: TestResponse = client.post(
            "/api/auth/register",
            json={
                "username": "cleartest",
                "email": "cleartest@example.com",
                "phone_number": "1234567890",
                "imei": "12345678901234",
                "password": "ValidPass@123",
            },
        )
        assert response.status_code == 201

        response = client.post(
            "/api/auth/login",
            json={"username": "cleartest", "password": "WrongPass@123"},
        )
        assert response.status_code == 401

        with client.application.app_context():
            user = User.query.filter_by(username="cleartest").one()
            totp = pyotp.TOTP(user.two_factor_secret)
            token = totp.now()

        response = client.post(
            "/api/auth/login",
            json={
                "username": "cleartest",
                "password": "ValidPass@123",
                "token": token,
            },
        )
        assert response.status_code == 200

        response = client.post(
            "/api/auth/login",
            json={"username": "cleartest", "password": "WrongPass@123"},
        )
        assert response.status_code == 401


class TestSecurityAuditLogging:
    """Tests for security audit logging."""

    def test_successful_login_logged(self, client: FlaskClient) -> None:
        """Successful login should be logged."""
        import pyotp

        response: TestResponse = client.post(
            "/api/auth/register",
            json={
                "username": "successlog",
                "email": "successlog@example.com",
                "phone_number": "1234567890",
                "imei": "12345678901234",
                "password": "ValidPass@123",
            },
        )
        assert response.status_code == 201

        with client.application.app_context():
            user = User.query.filter_by(username="successlog").one()
            totp = pyotp.TOTP(user.two_factor_secret)
            token = totp.now()

        response = client.post(
            "/api/auth/login",
            json={
                "username": "successlog",
                "password": "ValidPass@123",
                "token": token,
            },
        )
        assert response.status_code == 200

        with client.application.app_context():
            from src.app.models import AuditLog

            logs = (
                AuditLog.query.filter_by(
                    event_type="successful_login", username="successlog"
                )
                .order_by(AuditLog.created_at.desc())
                .all()
            )
            assert len(logs) > 0

    def test_role_change_logged(self, client: FlaskClient) -> None:
        """Role changes should be logged to audit trail."""
        import pyotp

        admin_response: TestResponse = client.post(
            "/api/auth/register",
            json={
                "username": "admin1",
                "email": "admin1@example.com",
                "phone_number": "1234567890",
                "imei": "12345678901234",
                "password": "AdminPass@123",
                "role": "admin",
            },
        )
        assert admin_response.status_code == 201

        user_response: TestResponse = client.post(
            "/api/auth/register",
            json={
                "username": "promoteme",
                "email": "promoteme@example.com",
                "phone_number": "1234567890",
                "imei": "12345678901234",
                "password": "ValidPass@123",
            },
        )
        assert user_response.status_code == 201

        with client.application.app_context():
            admin_user = User.query.filter_by(username="admin1").one()
            totp = pyotp.TOTP(admin_user.two_factor_secret)
            token = totp.now()

        login_response: TestResponse = client.post(
            "/api/auth/login",
            json={
                "username": "admin1",
                "password": "AdminPass@123",
                "token": token,
            },
        )
        assert login_response.status_code == 200

        role_response: TestResponse = client.patch(
            "/api/manager/users/promoteme/role",
            json={"role": "manager"},
        )
        assert role_response.status_code == 200

        with client.application.app_context():
            from src.app.models import AuditLog

            logs = (
                AuditLog.query.filter_by(event_type="role_change", username="admin1")
                .order_by(AuditLog.created_at.desc())
                .all()
            )
            assert len(logs) > 0
            assert "promoteme" in logs[0].message
            assert "manager" in logs[0].message

    def test_unauthorized_access_logged(self, client: FlaskClient) -> None:
        """Unauthorized access attempts should be logged."""
        response: TestResponse = client.post(
            "/api/auth/register",
            json={
                "username": "normaluser",
                "email": "normaluser@example.com",
                "phone_number": "1234567890",
                "imei": "12345678901234",
                "password": "ValidPass@123",
            },
        )
        assert response.status_code == 201

        import pyotp

        with client.application.app_context():
            user = User.query.filter_by(username="normaluser").one()
            totp = pyotp.TOTP(user.two_factor_secret)
            token = totp.now()

        login_response: TestResponse = client.post(
            "/api/auth/login",
            json={
                "username": "normaluser",
                "password": "ValidPass@123",
                "token": token,
            },
        )
        assert login_response.status_code == 200

        response = client.get("/api/manager/users")
        assert response.status_code == 403

        with client.application.app_context():
            from src.app.models import AuditLog

            logs = (
                AuditLog.query.filter_by(
                    event_type="unauthorized_access", username="normaluser"
                )
                .order_by(AuditLog.created_at.desc())
                .all()
            )
            assert len(logs) > 0
