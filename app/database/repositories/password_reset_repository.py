from datetime import datetime, timedelta, timezone
from typing import Optional
from app.database.repositories.base_repository import BaseRepository


class PasswordResetRepository(BaseRepository):

    OTP_EXPIRY_MINUTES = 10

    def create_token(self, user_id: int, token: str = None) -> str:
        import secrets
        # Invalidate old tokens for this user
        self.execute_write(
            "UPDATE password_reset_tokens SET used = TRUE WHERE user_id = %s",
            (user_id,),
        )
        if token is None:
            token = secrets.token_hex(32)

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
        self.execute_write(
            """
            INSERT INTO password_reset_tokens (user_id, token, expires_at)
            VALUES (%s, %s, %s)
            """,
            (user_id, token, expires_at),
        )
        return token

    def get_valid_token(self, token: str) -> Optional[dict]:
        row = self.execute_one(
            """
            SELECT * FROM password_reset_tokens
            WHERE token = %s
              AND used = FALSE
              AND expires_at > NOW()
            """,
            (token,),
        )
        return row

    def mark_used(self, token: str) -> None:
        self.execute_write(
            "UPDATE password_reset_tokens SET used = TRUE WHERE token = %s",
            (token,),
        )

    def cleanup_expired(self) -> None:
        self.execute_write(
            "DELETE FROM password_reset_tokens WHERE expires_at < NOW() OR used = TRUE",
        )