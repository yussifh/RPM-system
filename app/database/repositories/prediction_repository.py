"""
prediction_repository.py
--------------------------
Data access for the `predictions` table — AI risk output, decoupled
from raw vitals (see schema design notes in Phase 2).
"""

from decimal import Decimal

from app.database.repositories.base_repository import BaseRepository
from app.database.models import Prediction


class PredictionRepository(BaseRepository):

    def create(self, patient_id: int, vitals_id: int, disease_type: str,
               risk_score: float, risk_level: str, model_version: str) -> int:
        sql = """
            INSERT INTO predictions
                (patient_id, vitals_id, disease_type, risk_score, risk_level, model_version)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        result = self.execute_write(
            sql, (patient_id, vitals_id, disease_type,
                  Decimal(str(risk_score)), risk_level, model_version)
        )
        return result["lastrowid"]

    def get_latest_by_disease(self, patient_id: int, disease_type: str) -> Prediction | None:
        """
        Used by both the patient dashboard ("your current stroke risk is...")
        and the doctor dashboard's patient summary cards.
        """
        row = self.execute_one(
            """
            SELECT * FROM predictions
            WHERE patient_id = %s AND disease_type = %s
            ORDER BY predicted_at DESC
            LIMIT 1
            """,
            (patient_id, disease_type),
        )
        return Prediction.from_row(row) if row else None

    def get_latest_all_diseases(self, patient_id: int) -> list[Prediction]:
        """
        One query, returns the most recent prediction per disease type
        for a patient — powers the "3-card risk summary" on both the
        patient and doctor dashboards.
        """
        sql = """
            SELECT p1.*
            FROM predictions p1
            INNER JOIN (
                SELECT disease_type, MAX(predicted_at) AS max_time
                FROM predictions
                WHERE patient_id = %s
                GROUP BY disease_type
            ) latest
              ON p1.disease_type = latest.disease_type
             AND p1.predicted_at = latest.max_time
            WHERE p1.patient_id = %s
        """
        rows = self.execute_query(sql, (patient_id, patient_id))
        return [Prediction.from_row(r) for r in rows]

    def get_history(self, patient_id: int, disease_type: str, limit: int = 30) -> list[Prediction]:
        """Powers the risk-trend-over-time chart for a specific disease."""
        rows = self.execute_query(
            """
            SELECT * FROM (
                SELECT * FROM predictions
                WHERE patient_id = %s AND disease_type = %s
                ORDER BY predicted_at DESC
                LIMIT %s
            ) recent
            ORDER BY predicted_at ASC
            """,
            (patient_id, disease_type, limit),
        )
        return [Prediction.from_row(r) for r in rows]

    def list_high_risk_patients(self, doctor_id: int) -> list[dict]:
        """
        Doctor dashboard "at-risk patients" widget: latest prediction per
        patient/disease where risk_level is high or critical, restricted
        to this doctor's assigned patients.
        """
        sql = """
            SELECT pr.*, u.full_name AS patient_name
            FROM predictions pr
            INNER JOIN (
                SELECT patient_id, disease_type, MAX(predicted_at) AS max_time
                FROM predictions
                GROUP BY patient_id, disease_type
            ) latest
              ON pr.patient_id = latest.patient_id
             AND pr.disease_type = latest.disease_type
             AND pr.predicted_at = latest.max_time
            JOIN patients p ON p.user_id = pr.patient_id
            JOIN users u ON u.id = pr.patient_id
            WHERE p.assigned_doctor_id = %s
              AND pr.risk_level IN ('high', 'critical')
            ORDER BY pr.risk_score DESC
        """
        return self.execute_query(sql, (doctor_id,))
