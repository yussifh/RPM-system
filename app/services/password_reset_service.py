"""
password_reset_service.py
"""
from typing import Optional
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.password_reset_repository import PasswordResetRepository
from app.database.repositories.audit_log_repository import AuditLogRepository
from app.core.security import PasswordHasher
from app.core.exceptions import ValidationError

class PasswordResetService:
    def __init__(self, user_repo=None, reset_repo=None, audit_repo=None):
        self.user_repo  = user_repo  or UserRepository()
        self.reset_repo = reset_repo or PasswordResetRepository()
        self.audit_repo = audit_repo or AuditLogRepository()

    def request_reset(self, email: str) -> Optional[str]:
        email = email.strip().lower()
        user  = self.user_repo.get_by_email(email)
        if user is None or not user.is_active:
            self.audit_repo.log("PASSWORD_RESET_REQUEST_FAILED", details=f"email={email}")
            return None
        token = self.reset_repo.create_token(user.id)
        self.audit_repo.log("PASSWORD_RESET_REQUESTED", user_id=user.id)
        return token

    def reset_password(self, token: str, new_password: str) -> bool:
        if not token or not token.strip():
            raise ValidationError("Please enter your reset token.")
        if not self._is_strong_password(new_password):
            raise ValidationError("Password must be at least 8 characters and include a letter and a number.")
        token_row = self.reset_repo.get_valid_token(token.strip())
        if token_row is None:
            raise ValidationError(f"This reset token is invalid or has expired. Please request a new one (tokens expire after {PasswordResetRepository.OTP_EXPIRY_MINUTES} minutes).")
        new_hash = PasswordHasher.hash_password(new_password)
        self.user_repo.update_password(token_row["user_id"], new_hash)
        self.reset_repo.mark_used(token.strip())
        self.audit_repo.log("PASSWORD_RESET_SUCCESS", user_id=token_row["user_id"])
        return True

    def get_user_by_token(self, token: str):
        token_row = self.reset_repo.get_valid_token(token.strip())
        if token_row is None:
            return None
        return self.user_repo.get_by_id(token_row["user_id"])

    @staticmethod
    def _is_strong_password(password: str) -> bool:
        if len(password) < 8:
            return False
        return any(c.isalpha() for c in password) and any(c.isdigit() for c in password)
