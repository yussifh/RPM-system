"""
patient_repository.py
----------------------
Data access for the `patients` table (extends `users` where role='patient').
"""

from typing import Optional

from app.database.repositories.base_repository import BaseRepository
from app.database.models import Patient
from app.core.exceptions import RecordNotFoundError


class PatientRepository(BaseRepository):

    def create(self, user_id: int, date_of_birth, gender: str,
               assigned_doctor_id: Optional[int], chronic_conditions: list[str],
               emergency_contact: Optional[str] = None) -> None:
        sql = """
            INSERT INTO patients
                (user_id, date_of_birth, gender, assigned_doctor_id,
                 chronic_conditions, emergency_contact)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        conditions_csv = ",".join(chronic_conditions)  # MySQL SET column accepts CSV string
        self.execute_write(sql, (user_id, date_of_birth, gender, assigned_doctor_id,
                                  conditions_csv, emergency_contact))

    def get_by_user_id(self, user_id: int) -> Patient:
        row = self.execute_one("SELECT * FROM patients WHERE user_id = %s", (user_id,))
        if row is None:
            raise RecordNotFoundError(f"No patient profile found for user_id={user_id}")
        return Patient.from_row(row)

    def list_by_doctor(self, doctor_id: int) -> list[Patient]:
        """
        Doctor dashboard's primary query: "give me all my assigned patients".
        Joins users for display name/contact info.
        """
        sql = """
            SELECT p.*, u.full_name, u.email, u.is_active
            FROM patients p
            JOIN users u ON u.id = p.user_id
            WHERE p.assigned_doctor_id = %s AND u.is_active = TRUE
            ORDER BY u.full_name
        """
        rows = self.execute_query(sql, (doctor_id,))
        return [Patient.from_row(r) for r in rows]

    def list_all(self) -> list[Patient]:
        """Admin-facing: view of every patient in the system."""
        sql = """
            SELECT p.*, u.full_name, u.email, u.is_active
            FROM patients p
            JOIN users u ON u.id = p.user_id
            ORDER BY u.full_name
        """
        rows = self.execute_query(sql)
        return [Patient.from_row(r) for r in rows]

    def reassign_doctor(self, patient_user_id: int, new_doctor_id: int) -> None:
        """Used by Admin when reassigning a patient to a different doctor."""
        self.execute_write(
            "UPDATE patients SET assigned_doctor_id = %s WHERE user_id = %s",
            (new_doctor_id, patient_user_id),
        )

    def update_conditions(self, patient_user_id: int, chronic_conditions: list[str]) -> None:
        conditions_csv = ",".join(chronic_conditions)
        self.execute_write(
            "UPDATE patients SET chronic_conditions = %s WHERE user_id = %s",
            (conditions_csv, patient_user_id),
        )

    def update_emergency_contact(self, patient_user_id: int, emergency_contact: str = None) -> None:
        self.execute_write(
            "UPDATE patients SET emergency_contact = %s WHERE user_id = %s",
            (emergency_contact, patient_user_id),
        )
