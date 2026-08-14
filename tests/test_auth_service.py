"""
test_auth_service.py
---------------------
Unit tests for AuthService — login, registration, and password validation.
Uses mock repositories so no database connection is required.
"""

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import MagicMock, patch
from datetime import date

from app.core.exceptions import AuthenticationError, ValidationError, DuplicateRecordError
from app.services.auth_service import AuthService
from app.database.models import User


# ── Helpers ───────────────────────────────────────────────────────
def _make_user(role="patient", is_active=True):
    u = MagicMock(spec=User)
    u.id          = 1
    u.full_name   = "Test User"
    u.email       = "test@example.com"
    u.role        = role
    u.is_active   = is_active
    u.password_hash = "$2b$12$placeholder"
    return u


def _make_auth_service(user=None, email_exists=False):
    user_repo    = MagicMock()
    doctor_repo  = MagicMock()
    patient_repo = MagicMock()
    audit_repo   = MagicMock()

    user_repo.get_by_email.return_value  = user
    user_repo.email_exists.return_value  = email_exists
    user_repo.get_by_id.return_value     = user
    user_repo.create.return_value        = 1

    return AuthService(
        user_repo=user_repo,
        doctor_repo=doctor_repo,
        patient_repo=patient_repo,
        audit_repo=audit_repo,
    )


# ── Authentication Tests ──────────────────────────────────────────
class TestAuthenticate:

    def test_login_fails_unknown_email(self):
        svc = _make_auth_service(user=None)
        with pytest.raises(AuthenticationError):
            svc.authenticate("nobody@example.com", "password123")

    def test_login_fails_inactive_account(self):
        user = _make_user(is_active=False)
        svc  = _make_auth_service(user=user)
        with pytest.raises(AuthenticationError, match="deactivated"):
            svc.authenticate("test@example.com", "password123")

    @patch("app.services.auth_service.PasswordHasher.verify_password", return_value=False)
    def test_login_fails_wrong_password(self, _):
        user = _make_user()
        svc  = _make_auth_service(user=user)
        with pytest.raises(AuthenticationError):
            svc.authenticate("test@example.com", "wrongpassword")

    @patch("app.services.auth_service.PasswordHasher.verify_password", return_value=True)
    def test_login_succeeds(self, _):
        user = _make_user()
        svc  = _make_auth_service(user=user)
        result = svc.authenticate("test@example.com", "password123")
        assert result.full_name == "Test User"

    @patch("app.services.auth_service.PasswordHasher.verify_password", return_value=True)
    def test_login_logs_success(self, _):
        user = _make_user()
        svc  = _make_auth_service(user=user)
        svc.authenticate("test@example.com", "password123")
        svc.audit_repo.log.assert_called_with("LOGIN_SUCCESS", user_id=1)

    def test_login_logs_failure(self):
        svc = _make_auth_service(user=None)
        with pytest.raises(AuthenticationError):
            svc.authenticate("nobody@example.com", "pass")
        svc.audit_repo.log.assert_called()


# ── Registration Tests ────────────────────────────────────────────
class TestRegisterPatient:

    @patch("app.services.auth_service.PasswordHasher.hash_password", return_value="hashed")
    def test_register_succeeds(self, _):
        user = _make_user()
        svc  = _make_auth_service(user=user, email_exists=False)
        result = svc.register_patient(
            full_name="John Mensah", email="john@example.com",
            password="password1", date_of_birth=date(1990,1,1),
            gender="male", chronic_conditions=["diabetes"],
        )
        assert result is not None

    def test_register_fails_duplicate_email(self):
        svc = _make_auth_service(email_exists=True)
        with pytest.raises(DuplicateRecordError):
            svc.register_patient(
                full_name="John", email="john@example.com",
                password="password1", date_of_birth=date(1990,1,1),
                gender="male", chronic_conditions=["diabetes"],
            )

    def test_register_fails_no_conditions(self):
        svc = _make_auth_service(email_exists=False)
        with pytest.raises(ValidationError, match="chronic condition"):
            svc.register_patient(
                full_name="John", email="john@example.com",
                password="password1", date_of_birth=date(1990,1,1),
                gender="male", chronic_conditions=[],
            )

    def test_register_fails_weak_password(self):
        svc = _make_auth_service(email_exists=False)
        with pytest.raises(ValidationError, match="Password"):
            svc.register_patient(
                full_name="John", email="john@example.com",
                password="abc", date_of_birth=date(1990,1,1),
                gender="male", chronic_conditions=["diabetes"],
            )

    def test_register_fails_short_name(self):
        svc = _make_auth_service(email_exists=False)
        with pytest.raises(ValidationError, match="Full name"):
            svc.register_patient(
                full_name="J", email="john@example.com",
                password="password1", date_of_birth=date(1990,1,1),
                gender="male", chronic_conditions=["diabetes"],
            )

    def test_register_fails_invalid_email(self):
        svc = _make_auth_service(email_exists=False)
        with pytest.raises(ValidationError, match="email"):
            svc.register_patient(
                full_name="John Doe", email="notanemail",
                password="password1", date_of_birth=date(1990,1,1),
                gender="male", chronic_conditions=["diabetes"],
            )


# ── Password Validation Tests ─────────────────────────────────────
class TestPasswordValidation:

    def test_strong_password_accepted(self):
        assert AuthService._is_strong_password("password1") is True
        assert AuthService._is_strong_password("MyP@ssw0rd") is True

    def test_too_short_rejected(self):
        assert AuthService._is_strong_password("pass1") is False

    def test_no_digit_rejected(self):
        assert AuthService._is_strong_password("password") is False

    def test_no_letter_rejected(self):
        assert AuthService._is_strong_password("12345678") is False

    def test_exactly_8_chars_accepted(self):
        assert AuthService._is_strong_password("abcdef1g") is True
