"""
emergency_contact_repository.py
--------------------------------
Data access for the emergency_notifications table.
Tracks alerts sent to patients' emergency contacts when vitals are critical.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.database.repositories.base_repository import BaseRepository


@dataclass
class EmergencyNotification:
    id: Optional[int]
    patient_id: int
    emergency_contact: str
    severity: str
    message: str
    vital_snapshot: Optional[str]
    notification_type: str
    status: str
    sent_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    created_at: Optional[datetime]
    patient_name: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "EmergencyNotification":
        return cls(
            id=row["id"],
            patient_id=row["patient_id"],
            emergency_contact=row["emergency_contact"],
            severity=row["severity"],
            message=row["message"],
            vital_snapshot=row.get("vital_snapshot"),
            notification_type=row.get("notification_type", "sms"),
            status=row.get("status", "pending"),
            sent_at=row.get("sent_at"),
            acknowledged_at=row.get("acknowledged_at"),
            created_at=row.get("created_at"),
            patient_name=row.get("patient_name"),
        )


class EmergencyContactRepository(BaseRepository):

    def create(self, patient_id: int, emergency_contact: str,
               severity: str, message: str, vital_snapshot: str = None,
               notification_type: str = "sms") -> int:
        result = self.execute_write(
            """
            INSERT INTO emergency_notifications
                (patient_id, emergency_contact, severity, message,
                 vital_snapshot, notification_type, status, sent_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'sent', NOW())
            """,
            (patient_id, emergency_contact, severity, message,
             vital_snapshot, notification_type),
        )
        return result["lastrowid"]

    def list_for_patient(self, patient_id: int, limit: int = 20) -> list:
        rows = self.execute_query(
            """
            SELECT en.*, u.full_name AS patient_name
            FROM emergency_notifications en
            JOIN users u ON u.id = en.patient_id
            WHERE en.patient_id = %s
            ORDER BY en.created_at DESC
            LIMIT %s
            """,
            (patient_id, limit),
        )
        return [EmergencyNotification.from_row(r) for r in rows]

    def list_all(self, limit: int = 100) -> list:
        rows = self.execute_query(
            """
            SELECT en.*, u.full_name AS patient_name
            FROM emergency_notifications en
            JOIN users u ON u.id = en.patient_id
            ORDER BY en.created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [EmergencyNotification.from_row(r) for r in rows]

    def list_pending(self) -> list:
        rows = self.execute_query(
            """
            SELECT en.*, u.full_name AS patient_name
            FROM emergency_notifications en
            JOIN users u ON u.id = en.patient_id
            WHERE en.status = 'pending'
            ORDER BY en.created_at DESC
            """
        )
        return [EmergencyNotification.from_row(r) for r in rows]

    def acknowledge(self, notification_id: int) -> None:
        self.execute_write(
            """
            UPDATE emergency_notifications
            SET status = 'acknowledged', acknowledged_at = NOW()
            WHERE id = %s
            """,
            (notification_id,),
        )

    def count_by_severity(self) -> dict:
        rows = self.execute_query(
            """
            SELECT severity, COUNT(*) AS count
            FROM emergency_notifications
            GROUP BY severity
            """
        )
        return {row["severity"]: row["count"] for row in rows}
