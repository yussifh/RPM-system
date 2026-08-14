"""
vitals_repository.py
---------------------
Data access for the `vitals_records` table — the append-only clinical
time-series data patients submit.

Design decision: NO update() or delete() methods exposed here on
purpose. Vitals records represent a clinical history; once submitted,
they should never be silently altered. Corrections, if ever needed,
should be handled as a new record + an audit_log entry, not an
in-place edit — this preserves an honest audit trail.
"""

from app.database.repositories.base_repository import BaseRepository
from app.database.models import VitalsRecord
from app.core.exceptions import RecordNotFoundError


class VitalsRepository(BaseRepository):

    def create(self, patient_id: int, systolic_bp=None, diastolic_bp=None,
               heart_rate=None, glucose_level=None, weight_kg=None,
               temperature_c=None, oxygen_saturation=None,
               symptoms=None, notes=None) -> int:
        sql = """
            INSERT INTO vitals_records
                (patient_id, systolic_bp, diastolic_bp, heart_rate,
                 glucose_level, weight_kg, temperature_c,
                 oxygen_saturation, symptoms, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (patient_id, systolic_bp, diastolic_bp, heart_rate,
                   glucose_level, weight_kg, temperature_c,
                   oxygen_saturation, symptoms, notes)
        result = self.execute_write(sql, params)
        return result["lastrowid"]

    def get_by_id(self, vitals_id: int) -> VitalsRecord:
        row = self.execute_one("SELECT * FROM vitals_records WHERE id = %s", (vitals_id,))
        if row is None:
            raise RecordNotFoundError(f"No vitals record found with id={vitals_id}")
        return VitalsRecord.from_row(row)

    def get_latest_for_patient(self, patient_id: int) -> VitalsRecord | None:
        """Used by the risk_engine — always predicts off the most recent reading."""
        row = self.execute_one(
            """
            SELECT * FROM vitals_records
            WHERE patient_id = %s
            ORDER BY recorded_at DESC
            LIMIT 1
            """,
            (patient_id,),
        )
        return VitalsRecord.from_row(row) if row else None

    def get_history(self, patient_id: int, limit: int = 30) -> list[VitalsRecord]:
        """
        Powers both the patient's personal trend charts and the
        deterioration-detection logic (rolling averages over recent
        readings). Returned oldest-first so charts plot left-to-right
        chronologically without the caller needing to reverse it.
        """
        rows = self.execute_query(
            """
            SELECT * FROM (
                SELECT * FROM vitals_records
                WHERE patient_id = %s
                ORDER BY recorded_at DESC
                LIMIT %s
            ) recent
            ORDER BY recorded_at ASC
            """,
            (patient_id, limit),
        )
        return [VitalsRecord.from_row(r) for r in rows]

    def get_history_between(self, patient_id: int, start_date, end_date) -> list[VitalsRecord]:
        """Used for doctor-selected custom date-range reports."""
        rows = self.execute_query(
            """
            SELECT * FROM vitals_records
            WHERE patient_id = %s AND recorded_at BETWEEN %s AND %s
            ORDER BY recorded_at ASC
            """,
            (patient_id, start_date, end_date),
        )
        return [VitalsRecord.from_row(r) for r in rows]

    def get_all_with_patients(self, limit: int = 500) -> list[dict]:
        """Admin report: all vitals records with patient names."""
        return self.execute_query(
            """
            SELECT v.*, u.full_name AS patient_name, u.email AS patient_email,
                   p.gender, p.chronic_conditions
            FROM vitals_records v
            JOIN users u ON u.id = v.patient_id
            JOIN patients p ON p.user_id = v.patient_id
            ORDER BY v.recorded_at DESC
            LIMIT %s
            """,
            (limit,),
        )

    def get_summary_stats(self) -> dict:
        """Admin report: aggregate vitals statistics."""
        row = self.execute_one(
            """
            SELECT
                COUNT(*) AS total_readings,
                COUNT(DISTINCT patient_id) AS patients_with_readings,
                ROUND(AVG(systolic_bp),1) AS avg_systolic,
                ROUND(AVG(diastolic_bp),1) AS avg_diastolic,
                ROUND(AVG(heart_rate),1) AS avg_heart_rate,
                ROUND(AVG(glucose_level),1) AS avg_glucose,
                MIN(recorded_at) AS earliest_reading,
                MAX(recorded_at) AS latest_reading
            FROM vitals_records
            """
        )
        return row or {}
