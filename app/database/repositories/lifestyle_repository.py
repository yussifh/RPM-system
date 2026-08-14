"""
lifestyle_repository.py
------------------------
Data access for lifestyle_records table.
Stores BMI, smoking status, cholesterol, exercise, diet.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.database.repositories.base_repository import BaseRepository


@dataclass
class LifestyleRecord:
    id: Optional[int]
    patient_id: int
    recorded_at: Optional[datetime]
    height_cm: Optional[Decimal]
    weight_kg: Optional[Decimal]
    bmi: Optional[Decimal]
    smoking_status: Optional[str]
    cigarettes_per_day: Optional[int]
    alcohol_units_week: Optional[int]
    total_cholesterol: Optional[Decimal]
    hdl_cholesterol: Optional[Decimal]
    ldl_cholesterol: Optional[Decimal]
    exercise_minutes_week: Optional[int]
    activity_level: Optional[str]
    diet_type: Optional[str]
    notes: Optional[str]

    @classmethod
    def from_row(cls, row: dict) -> "LifestyleRecord":
        return cls(
            id=row["id"], patient_id=row["patient_id"],
            recorded_at=row.get("recorded_at"),
            height_cm=row.get("height_cm"), weight_kg=row.get("weight_kg"),
            bmi=row.get("bmi"), smoking_status=row.get("smoking_status"),
            cigarettes_per_day=row.get("cigarettes_per_day"),
            alcohol_units_week=row.get("alcohol_units_week"),
            total_cholesterol=row.get("total_cholesterol"),
            hdl_cholesterol=row.get("hdl_cholesterol"),
            ldl_cholesterol=row.get("ldl_cholesterol"),
            exercise_minutes_week=row.get("exercise_minutes_week"),
            activity_level=row.get("activity_level"),
            diet_type=row.get("diet_type"),
            notes=row.get("notes"),
        )


class LifestyleRepository(BaseRepository):

    def save(self, patient_id: int, height_cm: float = None,
             weight_kg: float = None, smoking_status: str = None,
             cigarettes_per_day: int = None, alcohol_units_week: int = None,
             total_cholesterol: float = None, hdl_cholesterol: float = None,
             ldl_cholesterol: float = None, exercise_minutes_week: int = None,
             activity_level: str = None, diet_type: str = None,
             notes: str = None) -> int:
        # Auto-calculate BMI
        bmi = None
        if height_cm and weight_kg and height_cm > 0:
            bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)

        result = self.execute_write(
            """
            INSERT INTO lifestyle_records
                (patient_id, height_cm, weight_kg, bmi, smoking_status,
                 cigarettes_per_day, alcohol_units_week, total_cholesterol,
                 hdl_cholesterol, ldl_cholesterol, exercise_minutes_week,
                 activity_level, diet_type, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (patient_id, height_cm, weight_kg, bmi, smoking_status,
             cigarettes_per_day, alcohol_units_week, total_cholesterol,
             hdl_cholesterol, ldl_cholesterol, exercise_minutes_week,
             activity_level, diet_type, notes),
        )
        return result["lastrowid"]

    def get_latest(self, patient_id: int) -> Optional[LifestyleRecord]:
        row = self.execute_one(
            """
            SELECT * FROM lifestyle_records
            WHERE patient_id = %s
            ORDER BY recorded_at DESC
            LIMIT 1
            """,
            (patient_id,),
        )
        return LifestyleRecord.from_row(row) if row else None

    def get_history(self, patient_id: int, limit: int = 10) -> list:
        rows = self.execute_query(
            """
            SELECT * FROM lifestyle_records
            WHERE patient_id = %s
            ORDER BY recorded_at DESC
            LIMIT %s
            """,
            (patient_id, limit),
        )
        return [LifestyleRecord.from_row(r) for r in rows]
