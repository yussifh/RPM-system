"""
alert_repository.py
---------------------
Data access for the `alerts` table — traceable to the prediction that
triggered them.
"""

from app.database.repositories.base_repository import BaseRepository
from app.database.models import Alert
from app.core.exceptions import RecordNotFoundError


class AlertRepository(BaseRepository):

    def create(self, patient_id: int, prediction_id: int, severity: str, message: str) -> int:
        sql = """
            INSERT INTO alerts (patient_id, prediction_id, severity, message)
            VALUES (%s, %s, %s, %s)
        """
        result = self.execute_write(sql, (patient_id, prediction_id, severity, message))
        return result["lastrowid"]

    def get_by_id(self, alert_id: int) -> Alert:
        row = self.execute_one("SELECT * FROM alerts WHERE id = %s", (alert_id,))
        if row is None:
            raise RecordNotFoundError(f"No alert found with id={alert_id}")
        return Alert.from_row(row)

    def list_open_for_doctor(self, doctor_id: int) -> list[dict]:
        """
        Doctor's primary alert queue: open alerts for their assigned
        patients, most severe and most recent first.
        """
        sql = """
            SELECT a.*, u.full_name AS patient_name
            FROM alerts a
            JOIN patients p ON p.user_id = a.patient_id
            JOIN users u ON u.id = a.patient_id
            WHERE p.assigned_doctor_id = %s AND a.status = 'open'
            ORDER BY
                FIELD(a.severity, 'critical', 'high', 'medium', 'low'),
                a.created_at DESC
        """
        return self.execute_query(sql, (doctor_id,))

    def list_for_patient(self, patient_id: int, limit: int = 20) -> list[Alert]:
        rows = self.execute_query(
            """
            SELECT * FROM alerts
            WHERE patient_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (patient_id, limit),
        )
        return [Alert.from_row(r) for r in rows]

    def acknowledge(self, alert_id: int, doctor_id: int) -> None:
        self.execute_write(
            """
            UPDATE alerts
            SET status = 'acknowledged', acknowledged_by = %s
            WHERE id = %s
            """,
            (doctor_id, alert_id),
        )

    def resolve(self, alert_id: int) -> None:
        self.execute_write(
            """
            UPDATE alerts
            SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (alert_id,),
        )

    def count_open_by_severity(self, doctor_id: int) -> dict[str, int]:
        """Powers small stat widgets like '3 Critical, 5 High' on the dashboard header."""
        rows = self.execute_query(
            """
            SELECT a.severity, COUNT(*) AS count
            FROM alerts a
            JOIN patients p ON p.user_id = a.patient_id
            WHERE p.assigned_doctor_id = %s AND a.status = 'open'
            GROUP BY a.severity
            """,
            (doctor_id,),
        )
        return {row["severity"]: row["count"] for row in rows}

    def count_open_by_severity_all(self) -> dict[str, int]:
        """
        System-wide equivalent of count_open_by_severity(), for the Admin
        overview dashboard — not scoped to any single doctor's patients.
        """
        rows = self.execute_query(
            """
            SELECT severity, COUNT(*) AS count
            FROM alerts
            WHERE status = 'open'
            GROUP BY severity
            """
        )
        return {row["severity"]: row["count"] for row in rows}

    def get_all_with_patients(self, limit: int = 500) -> list[dict]:
        """Admin report: all alerts with patient names."""
        return self.execute_query(
            """
            SELECT a.*, u.full_name AS patient_name, u.email AS patient_email,
                   doc.full_name AS acknowledged_by_name
            FROM alerts a
            JOIN users u ON u.id = a.patient_id
            LEFT JOIN users doc ON doc.id = a.acknowledged_by
            ORDER BY a.created_at DESC
            LIMIT %s
            """,
            (limit,),
        )

    def get_alert_stats(self) -> dict:
        """Admin report: alert statistics."""
        row = self.execute_one(
            """
            SELECT
                COUNT(*) AS total_alerts,
                SUM(status = 'open') AS open_count,
                SUM(status = 'acknowledged') AS acknowledged_count,
                SUM(status = 'resolved') AS resolved_count,
                COUNT(DISTINCT patient_id) AS patients_with_alerts
            FROM alerts
            """
        )
        return row or {}

    def count_acknowledged_by_doctor(self, doctor_id: int) -> int:
        row = self.execute_one(
            "SELECT COUNT(*) AS cnt FROM alerts WHERE acknowledged_by = %s",
            (doctor_id,),
        )
        return row["cnt"] if row else 0

    def count_open_for_doctor(self, doctor_id: int) -> int:
        row = self.execute_one(
            """
            SELECT COUNT(*) AS cnt FROM alerts a
            JOIN patients p ON p.user_id = a.patient_id
            WHERE p.assigned_doctor_id = %s AND a.status = 'open'
            """,
            (doctor_id,),
        )
        return row["cnt"] if row else 0
