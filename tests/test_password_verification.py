"""Full test coverage for password hashing, verification, and complexity."""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.app.services.security import (
    HashingError,
    PasswordComplexityError,
    SecurityService,
)

_VALID_PASSWORD = "ValidPass@123"
_PAYLOAD_BASE = {
    "email": "test@example.com",
    "phone_number": "1234567890",
    "imei": "12345678901234",
}


def _register(client: FlaskClient, username: str, password: str) -> TestResponse:
    return client.post(
        "/api/auth/register",
        json={**_PAYLOAD_BASE, "username": username, "email": f"{username}@x.com", "password": password},
    )


def _login(client: FlaskClient, username: str, password: str) -> TestResponse:
    return client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )


# ─── Argon2 hash / verify unit tests ─────────────────────────────────────────


class TestHashPassword:
    """SecurityService.hash_password unit tests."""

    def test_returns_argon2_formatted_string(self) -> None:
        """hash_password returns an Argon2id hash string."""
        svc = SecurityService()
        result = svc.hash_password(_VALID_PASSWORD)
        assert result.startswith("$argon2")

    def test_hashing_is_non_deterministic(self) -> None:
        """Two hashes of the same password differ due to salting."""
        svc = SecurityService()
        assert svc.hash_password(_VALID_PASSWORD) != svc.hash_password(_VALID_PASSWORD)

    def test_raises_complexity_error_for_weak_password(self) -> None:
        """hash_password rejects passwords that fail complexity rules."""
        svc = SecurityService()
        with pytest.raises(PasswordComplexityError):
            svc.hash_password("weak")


class TestVerifyPassword:
    """SecurityService.verify_password unit tests."""

    def test_correct_password_returns_true(self) -> None:
        """verify_password returns True when the password matches."""
        svc = SecurityService()
        h = svc.hash_password(_VALID_PASSWORD)
        assert svc.verify_password(h, _VALID_PASSWORD) is True

    def test_wrong_password_returns_false(self) -> None:
        """verify_password returns False when the password is wrong."""
        svc = SecurityService()
        h = svc.hash_password(_VALID_PASSWORD)
        assert svc.verify_password(h, "WrongPass@999") is False

    def test_empty_string_returns_false(self) -> None:
        """verify_password returns False for an empty-string attempt."""
        svc = SecurityService()
        h = svc.hash_password(_VALID_PASSWORD)
        assert svc.verify_password(h, "") is False

    def test_case_sensitive(self) -> None:
        """verify_password is case-sensitive."""
        svc = SecurityService()
        h = svc.hash_password(_VALID_PASSWORD)
        assert svc.verify_password(h, _VALID_PASSWORD.lower()) is False

    def test_both_salted_hashes_verify_correctly(self) -> None:
        """Two distinct hashes of the same password both verify correctly."""
        svc = SecurityService()
        h1 = svc.hash_password(_VALID_PASSWORD)
        h2 = svc.hash_password(_VALID_PASSWORD)
        assert svc.verify_password(h1, _VALID_PASSWORD) is True
        assert svc.verify_password(h2, _VALID_PASSWORD) is True

    def test_corrupted_hash_raises_hashing_error(self) -> None:
        """verify_password raises HashingError for a malformed hash."""
        svc = SecurityService()
        with pytest.raises(HashingError):
            svc.verify_password("not-a-valid-argon2-hash", _VALID_PASSWORD)


# ─── Complexity validation ────────────────────────────────────────────────────


class TestComplexityErrorMessages:
    """Each complexity rule produces a specific, actionable error message."""

    def test_short_password_mentions_length(self) -> None:
        svc = SecurityService()
        with pytest.raises(PasswordComplexityError, match="8 characters"):
            svc.validate_password_complexity("Ab1@")

    def test_long_password_mentions_length(self) -> None:
        svc = SecurityService()
        with pytest.raises(PasswordComplexityError, match="128 characters"):
            svc.validate_password_complexity("Ab1@" + "x" * 130)

    def test_missing_uppercase_mentions_uppercase(self) -> None:
        svc = SecurityService()
        with pytest.raises(PasswordComplexityError, match="uppercase"):
            svc.validate_password_complexity("validpass1@")

    def test_missing_lowercase_mentions_lowercase(self) -> None:
        svc = SecurityService()
        with pytest.raises(PasswordComplexityError, match="lowercase"):
            svc.validate_password_complexity("VALIDPASS1@")

    def test_missing_digit_mentions_digit(self) -> None:
        svc = SecurityService()
        with pytest.raises(PasswordComplexityError, match="digit"):
            svc.validate_password_complexity("ValidPass@!")

    def test_missing_special_char_mentions_special(self) -> None:
        svc = SecurityService()
        with pytest.raises(PasswordComplexityError, match="special"):
            svc.validate_password_complexity("ValidPass123")


# ─── Extended character acceptance (regression for whitelist bug) ─────────────


EXTENDED_CHAR_PASSWORDS = [
    ("underscore", "Test_1234!"),
    ("hyphen", "Test-1234!"),
    ("period", "Test.1234!"),
    ("hash", "Test1234!#"),
    ("space", "Test 1234!"),
    ("parentheses", "Test(1234!)"),
    ("brackets", "Test[1234!]"),
    ("caret", "Test^1234!"),
]


class TestExtendedCharacterPasswords:
    """Passwords with non-ASCII-letter characters beyond @$!%*?& must be accepted."""

    @pytest.mark.parametrize("label,password", EXTENDED_CHAR_PASSWORDS)
    def test_complexity_accepts_extended_chars(
        self, label: str, password: str
    ) -> None:
        """validate_password_complexity does not reject chars outside old whitelist."""
        svc = SecurityService()
        svc.validate_password_complexity(password)  # must not raise

    @pytest.mark.parametrize("label,password", EXTENDED_CHAR_PASSWORDS)
    def test_hash_then_verify_with_extended_chars(
        self, label: str, password: str
    ) -> None:
        """Hashing and verifying extended-char passwords round-trips correctly."""
        svc = SecurityService()
        h = svc.hash_password(password)
        assert svc.verify_password(h, password) is True
        assert svc.verify_password(h, password + "x") is False


# ─── Integration: register → login round trip ─────────────────────────────────


class TestRegistrationLoginRoundTrip:
    """Full HTTP round-trip tests for passwords with various character sets."""

    def test_standard_password_register_and_login(self, client: FlaskClient) -> None:
        """Standard password registers and logs in successfully."""
        assert _register(client, "std_user", "ValidPass@123").status_code == 201
        assert _login(client, "std_user", "ValidPass@123").status_code == 200

    def test_wrong_password_rejected_at_login(self, client: FlaskClient) -> None:
        """Login with wrong password returns 401."""
        _register(client, "wrong_pw", "ValidPass@123")
        assert _login(client, "wrong_pw", "WrongPass@999").status_code == 401

    def test_underscore_password_register_and_login(
        self, client: FlaskClient
    ) -> None:
        """Password with underscore registers and logs in correctly."""
        pw = "Test_Under1!"
        assert _register(client, "underscore_user", pw).status_code == 201
        assert _login(client, "underscore_user", pw).status_code == 200

    def test_hyphen_password_register_and_login(self, client: FlaskClient) -> None:
        """Password with hyphen registers and logs in correctly."""
        pw = "Test-Hyph1!"
        assert _register(client, "hyphen_user", pw).status_code == 201
        assert _login(client, "hyphen_user", pw).status_code == 200

    def test_space_password_register_and_login(self, client: FlaskClient) -> None:
        """Password with internal space registers and logs in correctly."""
        pw = "Test Pass1!"
        assert _register(client, "space_user", pw).status_code == 201
        assert _login(client, "space_user", pw).status_code == 200

    def test_wrong_password_after_extended_char_registration(
        self, client: FlaskClient
    ) -> None:
        """Wrong password is rejected even when registration used extended chars."""
        pw = "Test_Under1!"
        _register(client, "ext_wrong_pw", pw)
        assert _login(client, "ext_wrong_pw", "WrongPass@999").status_code == 401

    def test_previously_failing_password_now_accepted(
        self, client: FlaskClient
    ) -> None:
        """Regression: Test_1234! (underscore) was rejected before the fix."""
        pw = "Test_1234!"
        resp = _register(client, "regression_user", pw)
        assert resp.status_code == 201, f"Registration failed: {resp.get_json()}"
        assert _login(client, "regression_user", pw).status_code == 200
