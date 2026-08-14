"""
consent_repository.py
---------------------
Data access for patient_consents table.
Tracks patient consent for remote monitoring.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.database.repositories.base_repository import BaseRepository


@dataclass
class PatientConsent:
    id: Optional[int]
    patient_id: int
    consent_type: str
    consent_given: bool
    consent_text: Optional[str]
    ip_address: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def from_row(cls, row: dict) -> "PatientConsent":
        return cls(
            id=row["id"],
            patient_id=row["patient_id"],
            consent_type=row["consent_type"],
            consent_given=bool(row["consent_given"]),
            consent_text=row.get("consent_text"),
            ip_address=row.get("ip_address"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


class ConsentRepository(BaseRepository):

    def has_consent(self, patient_id: int, consent_type: str = "monitoring") -> bool:
        row = self.execute_one(
            """
            SELECT consent_given FROM patient_consents
            WHERE patient_id = %s AND consent_type = %s
            ORDER BY created_at DESC LIMIT 1
            """,
            (patient_id, consent_type),
        )
        return bool(row and row["consent_given"])

    def grant_consent(self, patient_id: int, consent_text: str = None,
                      consent_type: str = "monitoring", ip_address: str = None) -> int:
        result = self.execute_write(
            """
            INSERT INTO patient_consents
                (patient_id, consent_type, consent_given, consent_text, ip_address)
            VALUES (%s, %s, TRUE, %s, %s)
            """,
            (patient_id, consent_type, consent_text, ip_address),
        )
        return result["lastrowid"]

    def revoke_consent(self, patient_id: int, consent_type: str = "monitoring") -> None:
        self.execute_write(
            """
            INSERT INTO patient_consents
                (patient_id, consent_type, consent_given)
            VALUES (%s, %s, FALSE)
            """,
            (patient_id, consent_type),
        )

    def get_consent_history(self, patient_id: int) -> list:
        rows = self.execute_query(
            """
            SELECT * FROM patient_consents
            WHERE patient_id = %s
            ORDER BY created_at DESC
            """,
            (patient_id,),
        )
        return [PatientConsent.from_row(r) for r in rows]
