"""
user_repository.py
-------------------
Data access for the `users` table — the shared base table for all
three roles (admin/doctor/patient).

Note: this repository only touches `users`. Role-specific fields live
in DoctorRepository/PatientRepository. This mirrors the schema's table
inheritance design and keeps each repository focused on one table.
"""

from typing import Optional

from app.database.repositories.base_repository import BaseRepository
from app.database.models import User
from app.core.exceptions import RecordNotFoundError


class UserRepository(BaseRepository):

    def create(self, full_name: str, email: str, password_hash: str,
               role: str, phone_number: Optional[str] = None) -> int:
        """Inserts a new user and returns the new user's id."""
        sql = """
            INSERT INTO users (full_name, email, password_hash, role, phone_number)
            VALUES (%s, %s, %s, %s, %s)
        """
        result = self.execute_write(sql, (full_name, email, password_hash, role, phone_number))
        return result["lastrowid"]

    def get_by_id(self, user_id: int) -> User:
        row = self.execute_one("SELECT * FROM users WHERE id = %s", (user_id,))
        if row is None:
            raise RecordNotFoundError(f"No user found with id={user_id}")
        return User.from_row(row)

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Returns None (not an exception) when not found — this is the
        expected path during login, where "email not registered" is a
        normal outcome the auth_service needs to check, not an error.
        """
        row = self.execute_one("SELECT * FROM users WHERE email = %s", (email,))
        return User.from_row(row) if row else None

    def email_exists(self, email: str) -> bool:
        row = self.execute_one("SELECT id FROM users WHERE email = %s", (email,))
        return row is not None

    def list_by_role(self, role: str, active_only: bool = True) -> list[User]:
        sql = "SELECT * FROM users WHERE role = %s"
        params: tuple = (role,)
        if active_only:
            sql += " AND is_active = TRUE"
        sql += " ORDER BY full_name"
        rows = self.execute_query(sql, params)
        return [User.from_row(r) for r in rows]

    def update_password(self, user_id: int, new_password_hash: str) -> None:
        self.execute_write(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (new_password_hash, user_id),
        )

    def update_profile(self, user_id: int, full_name: str, phone_number: Optional[str]) -> None:
        self.execute_write(
            "UPDATE users SET full_name = %s, phone_number = %s WHERE id = %s",
            (full_name, phone_number, user_id),
        )

    def set_active_status(self, user_id: int, is_active: bool) -> None:
        """
        Used by Admin to deactivate/reactivate an account. Deliberately
        NOT a hard delete — healthcare systems should preserve historical
        records for audit purposes rather than destroying accounts.
        """
        self.execute_write(
            "UPDATE users SET is_active = %s WHERE id = %s",
            (is_active, user_id),
        )
