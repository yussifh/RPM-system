"""
teleconsultation_repository.py
-------------------------------
Data access for the `teleconsultations` table.
"""

import uuid
from datetime import datetime

from app.database.repositories.base_repository import BaseRepository


class TeleconsultationRepository(BaseRepository):

    def create(self, patient_user_id: int, doctor_user_id: int,
               appointment_id: int = None) -> int:
        room_id = uuid.uuid4().hex[:16]
        sql = """
            INSERT INTO teleconsultations (patient_user_id, doctor_user_id, appointment_id, room_id)
            VALUES (%s, %s, %s, %s)
        """
        result = self.execute_write(sql, (patient_user_id, doctor_user_id, appointment_id, room_id))
        return result["lastrowid"]

    def get_by_id(self, tele_id: int) -> dict | None:
        return self.execute_one("SELECT * FROM teleconsultations WHERE id = %s", (tele_id,))

    def get_by_room(self, room_id: str) -> dict | None:
        return self.execute_one("SELECT * FROM teleconsultations WHERE room_id = %s", (room_id,))

    def update_status(self, tele_id: int, status: str) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if status == "in_progress":
            self.execute_write(
                "UPDATE teleconsultations SET status=%s, started_at=%s WHERE id=%s",
                (status, now, tele_id),
            )
        elif status in ("completed", "cancelled"):
            self.execute_write(
                "UPDATE teleconsultations SET status=%s, ended_at=%s WHERE id=%s",
                (status, now, tele_id),
            )
        else:
            self.execute_write(
                "UPDATE teleconsultations SET status=%s WHERE id=%s",
                (status, tele_id),
            )

    def update_notes(self, tele_id: int, notes: str) -> None:
        self.execute_write("UPDATE teleconsultations SET notes=%s WHERE id=%s", (notes, tele_id))

    def list_for_doctor(self, doctor_user_id: int) -> list[dict]:
        sql = """
            SELECT t.*, u.full_name AS patient_name
            FROM teleconsultations t
            JOIN users u ON u.id = t.patient_user_id
            WHERE t.doctor_user_id = %s
            ORDER BY t.created_at DESC
        """
        return self.execute_query(sql, (doctor_user_id,))

    def list_for_patient(self, patient_user_id: int) -> list[dict]:
        sql = """
            SELECT t.*, d.full_name AS doctor_name
            FROM teleconsultations t
            JOIN users d ON d.id = t.doctor_user_id
            WHERE t.patient_user_id = %s
            ORDER BY t.created_at DESC
        """
        return self.execute_query(sql, (patient_user_id,))

    def list_active_for_doctor(self, doctor_user_id: int) -> list[dict]:
        sql = """
            SELECT t.*, u.full_name AS patient_name
            FROM teleconsultations t
            JOIN users u ON u.id = t.patient_user_id
            WHERE t.doctor_user_id = %s AND t.status IN ('scheduled', 'in_progress')
            ORDER BY t.created_at DESC
        """
        return self.execute_query(sql, (doctor_user_id,))

    def list_active_for_patient(self, patient_user_id: int) -> list[dict]:
        sql = """
            SELECT t.*, d.full_name AS doctor_name
            FROM teleconsultations t
            JOIN users d ON d.id = t.doctor_user_id
            WHERE t.patient_user_id = %s AND t.status IN ('scheduled', 'in_progress')
            ORDER BY t.created_at DESC
        """
        return self.execute_query(sql, (patient_user_id,))

    def count_all(self) -> int:
        row = self.execute_one("SELECT COUNT(*) AS cnt FROM teleconsultations")
        return row["cnt"] if row else 0
