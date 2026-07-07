"""
doctor_repository.py
---------------------
Data access for the `doctors` table (extends `users` where role='doctor').
"""

from typing import Optional

from app.database.repositories.base_repository import BaseRepository
from app.database.models import Doctor
from app.core.exceptions import RecordNotFoundError


class DoctorRepository(BaseRepository):

    def create(self, user_id: int, specialization: Optional[str], license_number: str) -> None:
        sql = """
            INSERT INTO doctors (user_id, specialization, license_number)
            VALUES (%s, %s, %s)
        """
        self.execute_write(sql, (user_id, specialization, license_number))

    def get_by_user_id(self, user_id: int) -> Doctor:
        row = self.execute_one("SELECT * FROM doctors WHERE user_id = %s", (user_id,))
        if row is None:
            raise RecordNotFoundError(f"No doctor profile found for user_id={user_id}")
        return Doctor.from_row(row)

    def list_all(self) -> list[Doctor]:
        """
        Joins with users so callers get name/email alongside doctor-specific
        fields in one query — this is the common case (e.g., populating an
        admin dropdown of doctors by name).
        """
        sql = """
            SELECT d.*, u.full_name, u.email, u.is_active
            FROM doctors d
            JOIN users u ON u.id = d.user_id
            WHERE u.is_active = TRUE
            ORDER BY u.full_name
        """
        rows = self.execute_query(sql)
        return [Doctor.from_row({k: v for k, v in r.items()
                                  if k in ("user_id", "specialization", "license_number")})
                for r in rows]

    def get_patient_count(self, doctor_id: int) -> int:
        """Used on the doctor's dashboard header and admin analytics."""
        row = self.execute_one(
            "SELECT COUNT(*) AS count FROM patients WHERE assigned_doctor_id = %s",
            (doctor_id,),
        )
        return row["count"] if row else 0
