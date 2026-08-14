"""
session_repository.py
---------------------
Data access for active_sessions table.
Tracks user sessions for management and security.
"""

import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.database.repositories.base_repository import BaseRepository


@dataclass
class ActiveSession:
    id: Optional[int]
    user_id: int
    session_token: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    login_at: Optional[datetime]
    last_activity: Optional[datetime]
    is_active: bool
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    user_email: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "ActiveSession":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            session_token=row["session_token"],
            ip_address=row.get("ip_address"),
            user_agent=row.get("user_agent"),
            login_at=row.get("login_at"),
            last_activity=row.get("last_activity"),
            is_active=bool(row["is_active"]),
            user_name=row.get("user_name"),
            user_role=row.get("user_role"),
            user_email=row.get("user_email"),
        )


class SessionRepository(BaseRepository):

    def create_session(self, user_id: int, ip_address: str = None,
                       user_agent: str = None) -> str:
        """Create a new session and return the token."""
        token = secrets.token_hex(32)
        self.execute_write(
            """
            INSERT INTO active_sessions
                (user_id, session_token, ip_address, user_agent)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, token, ip_address, user_agent),
        )
        return token

    def deactivate_session(self, session_token: str) -> None:
        self.execute_write(
            "UPDATE active_sessions SET is_active = FALSE WHERE session_token = %s",
            (session_token,),
        )

    def deactivate_all_for_user(self, user_id: int) -> None:
        self.execute_write(
            "UPDATE active_sessions SET is_active = FALSE WHERE user_id = %s",
            (user_id,),
        )

    def deactivate_session_by_id(self, session_id: int) -> None:
        self.execute_write(
            "UPDATE active_sessions SET is_active = FALSE WHERE id = %s",
            (session_id,),
        )

    def get_active_sessions(self) -> list:
        rows = self.execute_query(
            """
            SELECT s.*, u.full_name AS user_name, u.role AS user_role, u.email AS user_email
            FROM active_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.is_active = TRUE
            ORDER BY s.last_activity DESC
            """
        )
        return [ActiveSession.from_row(r) for r in rows]

    def get_sessions_for_user(self, user_id: int) -> list:
        rows = self.execute_query(
            """
            SELECT * FROM active_sessions
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY last_activity DESC
            """,
            (user_id,),
        )
        return [ActiveSession.from_row(r) for r in rows]

    def count_active_sessions(self) -> int:
        row = self.execute_one(
            "SELECT COUNT(*) AS cnt FROM active_sessions WHERE is_active = TRUE"
        )
        return row["cnt"] if row else 0

    def count_active_sessions_by_role(self) -> dict:
        rows = self.execute_query(
            """
            SELECT u.role, COUNT(*) AS count
            FROM active_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.is_active = TRUE
            GROUP BY u.role
            """
        )
        return {row["role"]: row["count"] for row in rows}
