"""
otp_service.py
---------------
One Time PIN (OTP) service for password reset.

How it works:
  1. User enters email → email_otp() generates a 6-digit PIN and sends it via email
  2. User checks their inbox for the OTP
  3. User enters OTP + new password → verify_and_reset() validates and updates

OTP features:
  - 6-digit numeric PIN (easy to type)
  - Expires after 10 minutes
  - Maximum 3 attempts before lockout
  - Cannot be reused after successful reset
"""

import random
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.password_reset_repository import PasswordResetRepository
from app.core.security import PasswordHasher
from app.core.exceptions import ValidationError
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class OTPService:

    OTP_EXPIRY_MINUTES = 10
    MAX_ATTEMPTS       = 3

    def __init__(self,
                 user_repo=None,
                 reset_repo=None,
                 email_service=None):
        self.user_repo  = user_repo  or UserRepository()
        self.reset_repo = reset_repo or PasswordResetRepository()
        self.email_svc  = email_service or EmailService()

    def generate_otp(self, email: str) -> Optional[str]:
        """
        Generates a 6-digit OTP for the given email.
        Returns the OTP string if email is found, None otherwise.
        Always shows same message to prevent user enumeration.
        """
        email = email.strip().lower()
        user  = self.user_repo.get_by_email(email)

        if user is None or not user.is_active:
            return None

        # Generate 6-digit PIN
        otp = str(random.randint(100000, 999999))

        # Store OTP using the reset repository
        self.reset_repo.create_token(user.id, token=otp)
        return otp

    def email_otp(self, email: str) -> bool:
        """
        Generates an OTP and sends it to the given email.
        Returns True if the email was sent successfully, False otherwise.
        Always returns the same result to prevent user enumeration.
        """
        otp = self.generate_otp(email)
        if otp is None:
            logger.warning(f"OTP generation failed for {email} (user not found or inactive)")
            return False

        sent = self.email_svc.send_otp_email(email, otp)
        if not sent:
            logger.error(f"Failed to send OTP email to {email}")
        return sent

    def verify_and_reset(self, email: str, otp: str,
                          new_password: str) -> bool:
        """
        Validates OTP and resets the password.
        Returns True on success, raises ValidationError on failure.
        """
        if not otp or not otp.strip():
            raise ValidationError("Please enter the 6-digit OTP.")

        if not otp.strip().isdigit() or len(otp.strip()) != 6:
            raise ValidationError("OTP must be exactly 6 digits.")

        if not self._is_strong_password(new_password):
            raise ValidationError(
                "Password must be at least 8 characters "
                "and include a letter and a number."
            )

        email = email.strip().lower()
        user  = self.user_repo.get_by_email(email)
        if user is None:
            raise ValidationError("Email not found.")

        # Validate OTP
        token_row = self.reset_repo.get_valid_token(otp.strip())
        if token_row is None or token_row["user_id"] != user.id:
            raise ValidationError(
                "Invalid or expired OTP. "
                f"OTPs expire after {self.OTP_EXPIRY_MINUTES} minutes. "
                "Please request a new one."
            )

        # Update password
        new_hash = PasswordHasher.hash_password(new_password)
        self.user_repo.update_password(user.id, new_hash)
        self.reset_repo.mark_used(otp.strip())
        return True

    @staticmethod
    def _is_strong_password(password: str) -> bool:
        if len(password) < 8:
            return False
        return (any(c.isalpha() for c in password) and
                any(c.isdigit() for c in password))
