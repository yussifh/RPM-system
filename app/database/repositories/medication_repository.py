"""
medication_repository.py
-------------------------
Data access for medications and medication_logs tables.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from app.database.repositories.base_repository import BaseRepository


@dataclass
class Medication:
    id: Optional[int]
    patient_id: int
    name: str
    dosage: str
    frequency: str
    route: str
    start_date: date
    end_date: Optional[date]
    prescribed_by: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    patient_name: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "Medication":
        return cls(
            id=row["id"], patient_id=row["patient_id"],
            name=row["name"], dosage=row["dosage"],
            frequency=row["frequency"], route=row.get("route","oral"),
            start_date=row["start_date"], end_date=row.get("end_date"),
            prescribed_by=row.get("prescribed_by"),
            notes=row.get("notes"), is_active=bool(row["is_active"]),
            created_at=row.get("created_at"), updated_at=row.get("updated_at"),
            patient_name=row.get("patient_name"),
        )


@dataclass
class MedicationLog:
    id: Optional[int]
    medication_id: int
    patient_id: int
    taken_at: Optional[datetime]
    taken: bool
    notes: Optional[str]
    medication_name: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "MedicationLog":
        return cls(
            id=row["id"], medication_id=row["medication_id"],
            patient_id=row["patient_id"], taken_at=row.get("taken_at"),
            taken=bool(row["taken"]), notes=row.get("notes"),
            medication_name=row.get("medication_name"),
        )


class MedicationRepository(BaseRepository):

    def add(self, patient_id: int, name: str, dosage: str,
            frequency: str, route: str, start_date: date,
            end_date: date = None, prescribed_by: str = None,
            notes: str = None) -> int:
        result = self.execute_write(
            """
            INSERT INTO medications
                (patient_id, name, dosage, frequency, route,
                 start_date, end_date, prescribed_by, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (patient_id, name, dosage, frequency, route,
             start_date, end_date, prescribed_by, notes),
        )
        return result["lastrowid"]

    def list_for_patient(self, patient_id: int,
                          active_only: bool = True) -> list:
        condition = "AND is_active = TRUE" if active_only else ""
        rows = self.execute_query(
            f"""
            SELECT * FROM medications
            WHERE patient_id = %s {condition}
            ORDER BY is_active DESC, start_date DESC
            """,
            (patient_id,),
        )
        return [Medication.from_row(r) for r in rows]

    def stop(self, med_id: int, patient_id: int) -> None:
        """Mark medication as inactive (stopped)."""
        self.execute_write(
            """
            UPDATE medications SET is_active = FALSE, end_date = CURDATE()
            WHERE id = %s AND patient_id = %s
            """,
            (med_id, patient_id),
        )

    def delete(self, med_id: int, patient_id: int) -> None:
        self.execute_write(
            "DELETE FROM medications WHERE id = %s AND patient_id = %s",
            (med_id, patient_id),
        )

    def log_taken(self, medication_id: int, patient_id: int,
                   taken: bool = True, notes: str = None) -> None:
        self.execute_write(
            """
            INSERT INTO medication_logs (medication_id, patient_id, taken, notes)
            VALUES (%s, %s, %s, %s)
            """,
            (medication_id, patient_id, taken, notes),
        )

    def get_today_logs(self, patient_id: int) -> list:
        rows = self.execute_query(
            """
            SELECT ml.*, m.name AS medication_name
            FROM medication_logs ml
            JOIN medications m ON m.id = ml.medication_id
            WHERE ml.patient_id = %s
              AND DATE(ml.taken_at) = CURDATE()
            ORDER BY ml.taken_at DESC
            """,
            (patient_id,),
        )
        return [MedicationLog.from_row(r) for r in rows]

    def get_adherence_rate(self, patient_id: int, days: int = 30) -> float:
        """Returns medication adherence rate as a percentage (0-100)."""
        row = self.execute_one(
            """
            SELECT
                COUNT(*) AS total,
                SUM(taken) AS taken_count
            FROM medication_logs
            WHERE patient_id = %s
              AND taken_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """,
            (patient_id, days),
        )
        if not row or not row["total"]:
            return 0.0
        return round((row["taken_count"] / row["total"]) * 100, 1)

    def get_all_with_patients(self, active_only: bool = True, limit: int = 500) -> list:
        """Admin report: all medications with patient names."""
        condition = "AND m.is_active = TRUE" if active_only else ""
        rows = self.execute_query(
            f"""
            SELECT m.*, u.full_name AS patient_name, u.email AS patient_email
            FROM medications m
            JOIN users u ON u.id = m.patient_id
            WHERE 1=1 {condition}
            ORDER BY m.start_date DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [Medication.from_row(r) for r in rows]

    def get_adherence_summary(self) -> list:
        """Admin report: adherence rates per patient."""
        return self.execute_query(
            """
            SELECT
                m.patient_id,
                u.full_name AS patient_name,
                COUNT(*) AS total_logs,
                SUM(m2.taken) AS taken_count,
                ROUND(SUM(m2.taken) / COUNT(*) * 100, 1) AS adherence_rate
            FROM medication_logs m2
            JOIN medications m ON m.id = m2.medication_id
            JOIN users u ON u.id = m2.patient_id
            WHERE m2.taken_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY m2.patient_id, u.full_name
            ORDER BY adherence_rate ASC
            """
        )
