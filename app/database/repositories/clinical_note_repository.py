"""
clinical_note_repository.py
------------------------------
Data access for the `clinical_notes` table — doctors' written
observations per patient.
"""

from app.database.repositories.base_repository import BaseRepository
from app.database.models import ClinicalNote


class ClinicalNoteRepository(BaseRepository):

    def create(self, doctor_id: int, patient_id: int, note: str) -> int:
        sql = """
            INSERT INTO clinical_notes (doctor_id, patient_id, note)
            VALUES (%s, %s, %s)
        """
        result = self.execute_write(sql, (doctor_id, patient_id, note))
        return result["lastrowid"]

    def list_for_patient(self, patient_id: int) -> list[dict]:
        """
        Joins in the authoring doctor's name so the UI doesn't need a
        second query per note when rendering a patient's note history.
        """
        sql = """
            SELECT cn.*, u.full_name AS doctor_name
            FROM clinical_notes cn
            JOIN users u ON u.id = cn.doctor_id
            WHERE cn.patient_id = %s
            ORDER BY cn.created_at DESC
        """
        return self.execute_query(sql, (patient_id,))
