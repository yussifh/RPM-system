"""
audit_log_repository.py
-------------------------
Data access for the `audit_logs` table — independent action trail,
used across the whole app (login attempts, data access, admin actions).
"""

from typing import Optional

from app.database.repositories.base_repository import BaseRepository
from app.database.models import AuditLog


class AuditLogRepository(BaseRepository):

    def log(self, action: str, user_id: Optional[int] = None,
            details: Optional[str] = None, ip_address: Optional[str] = None) -> None:
        """
        Fire-and-forget style logging call used throughout the Service
        layer, e.g.:
            audit_repo.log("LOGIN_SUCCESS", user_id=user.id)
            audit_repo.log("VITALS_SUBMITTED", user_id=patient.id, details=f"vitals_id={vid}")
        """
        sql = """
            INSERT INTO audit_logs (user_id, action, details, ip_address)
            VALUES (%s, %s, %s, %s)
        """
        self.execute_write(sql, (user_id, action, details, ip_address))

    def list_for_user(self, user_id: int, limit: int = 50) -> list[AuditLog]:
        rows = self.execute_query(
            """
            SELECT * FROM audit_logs
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        return [AuditLog.from_row(r) for r in rows]

    def list_recent(self, limit: int = 100) -> list[dict]:
        """Admin-facing system-wide audit view."""
        sql = """
            SELECT al.*, u.full_name AS user_name
            FROM audit_logs al
            LEFT JOIN users u ON u.id = al.user_id
            ORDER BY al.created_at DESC
            LIMIT %s
        """
        return self.execute_query(sql, (limit,))
