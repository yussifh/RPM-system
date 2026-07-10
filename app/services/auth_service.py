"""
auth_service.py
-----------------
Application-layer authentication logic: registration and credential
verification. Deliberately has NO Streamlit dependency — session
handling (a presentation concern) lives in app.core.security.SessionManager
instead. This separation means AuthService could be reused unchanged
behind a REST API or CLI, and can be unit-tested without mocking
Streamlit at all.
"""

from datetime import date
from typing import Optional

from app.core.security import PasswordHasher
from app.core.exceptions import AuthenticationError, ValidationError, DuplicateRecordError
from app.database.models import User
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.doctor_repository import DoctorRepository
from app.database.repositories.patient_repository import PatientRepository
from app.database.repositories.audit_log_repository import AuditLogRepository


class AuthService:

    def __init__(self,
                 user_repo: Optional[UserRepository] = None,
                 doctor_repo: Optional[DoctorRepository] = None,
                 patient_repo: Optional[PatientRepository] = None,
                 audit_repo: Optional[AuditLogRepository] = None):
        # Dependency injection with sensible defaults — makes this
        # class trivially testable by passing in mock repositories.
        self.user_repo = user_repo or UserRepository()
        self.doctor_repo = doctor_repo or DoctorRepository()
        self.patient_repo = patient_repo or PatientRepository()
        self.audit_repo = audit_repo or AuditLogRepository()

    # ==============================================================
    # Login
    # ==============================================================
    def authenticate(self, email: str, password: str) -> User:
        """
        Verifies credentials and returns the User on success.

        Security note: the error message is IDENTICAL whether the
        email doesn't exist or the password is wrong. This prevents
        user enumeration — an attacker probing emails one by one to
        discover which are registered.
        """
        email = email.strip().lower()
        user = self.user_repo.get_by_email(email)

        if user is None:
            self.audit_repo.log("LOGIN_FAILED", details=f"email={email} (unknown)")
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            self.audit_repo.log("LOGIN_FAILED", user_id=user.id, details="account inactive")
            raise AuthenticationError(
                "This account has been deactivated. Please contact an administrator."
            )

        if not PasswordHasher.verify_password(password, user.password_hash):
            self.audit_repo.log("LOGIN_FAILED", user_id=user.id, details="wrong password")
            raise AuthenticationError("Invalid email or password.")

        self.audit_repo.log("LOGIN_SUCCESS", user_id=user.id)
        return user

    # ==============================================================
    # Registration
    # ==============================================================
    def register_patient(self, full_name: str, email: str, password: str,
                          date_of_birth: date, gender: str,
                          chronic_conditions: list[str],
                          assigned_doctor_id: Optional[int] = None,
                          phone_number: Optional[str] = None,
                          emergency_contact: Optional[str] = None) -> User:
        """Self-service registration path used by the public Login/Register page."""
        email = email.strip().lower()
        self._validate_registration_input(full_name, email, password)
        if not chronic_conditions:
            raise ValidationError("Please select at least one chronic condition being managed.")
        if self.user_repo.email_exists(email):
            raise DuplicateRecordError("An account with this email already exists.")

        password_hash = PasswordHasher.hash_password(password)
        user_id = self.user_repo.create(full_name, email, password_hash,
                                         role="patient", phone_number=phone_number)
        self.patient_repo.create(user_id, date_of_birth, gender, assigned_doctor_id,
                                  chronic_conditions, emergency_contact)
        self.audit_repo.log("PATIENT_REGISTERED", user_id=user_id)
        return self.user_repo.get_by_id(user_id)

    def register_doctor(self, full_name: str, email: str, password: str,
                         specialization: Optional[str], license_number: str,
                         phone_number: Optional[str] = None) -> User:
        """
        Provisions a doctor account. NOT exposed on the public registration
        page — called only from the Admin module (Phase 8).
        """
        email = email.strip().lower()
        self._validate_registration_input(full_name, email, password)
        if not license_number or not license_number.strip():
            raise ValidationError("A medical license number is required.")
        if self.user_repo.email_exists(email):
            raise DuplicateRecordError("An account with this email already exists.")

        password_hash = PasswordHasher.hash_password(password)
        user_id = self.user_repo.create(full_name, email, password_hash,
                                         role="doctor", phone_number=phone_number)
        self.doctor_repo.create(user_id, specialization, license_number)
        self.audit_repo.log("DOCTOR_REGISTERED", user_id=user_id)
        return self.user_repo.get_by_id(user_id)

    def register_admin(self, full_name: str, email: str, password: str,
                        phone_number: Optional[str] = None) -> User:
        """
        Provisions an admin account. Intended for one-time system
        bootstrap (see scripts/bootstrap_admin.py) or use by an existing
        admin — never exposed on the public registration page.
        """
        email = email.strip().lower()
        self._validate_registration_input(full_name, email, password)
        if self.user_repo.email_exists(email):
            raise DuplicateRecordError("An account with this email already exists.")

        password_hash = PasswordHasher.hash_password(password)
        user_id = self.user_repo.create(full_name, email, password_hash,
                                         role="admin", phone_number=phone_number)
        self.audit_repo.log("ADMIN_REGISTERED", user_id=user_id)
        return self.user_repo.get_by_id(user_id)

    # ==============================================================
    # Password management
    # ==============================================================
    def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        user = self.user_repo.get_by_id(user_id)

        if not PasswordHasher.verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect.")

        if not self._is_strong_password(new_password):
            raise ValidationError(
                "New password must be at least 8 characters and include a letter and a number."
            )

        new_hash = PasswordHasher.hash_password(new_password)
        self.user_repo.update_password(user_id, new_hash)
        self.audit_repo.log("PASSWORD_CHANGED", user_id=user_id)

    # ==============================================================
    # Validation helpers
    # ==============================================================
    @staticmethod
    def _validate_registration_input(full_name: str, email: str, password: str) -> None:
        if not full_name or len(full_name.strip()) < 2:
            raise ValidationError("Full name must be at least 2 characters.")
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValidationError("Please enter a valid email address.")
        if not AuthService._is_strong_password(password):
            raise ValidationError(
                "Password must be at least 8 characters and include a letter and a number."
            )

    @staticmethod
    def _is_strong_password(password: str) -> bool:
        if len(password) < 8:
            return False
        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)
        return has_letter and has_digit
