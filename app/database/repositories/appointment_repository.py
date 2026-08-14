"""
appointment_repository.py
--------------------------
Data access layer for the appointments table.
"""

from dataclasses import dataclass
from datetime import date, time, datetime, timedelta
from typing import Optional

from app.database.repositories.base_repository import BaseRepository


@dataclass
class Appointment:
    id: Optional[int]
    doctor_id: int
    patient_id: int
    appointment_date: date
    appointment_time: time
    location: str
    reason: Optional[str]
    severity_level: Optional[str]
    status: str
    doctor_notes: Optional[str]
    patient_notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "Appointment":
        apt_time = row["appointment_time"]
        if isinstance(apt_time, timedelta):
            apt_time = (datetime.min + apt_time).time()
        return cls(
            id=row["id"],
            doctor_id=row["doctor_id"],
            patient_id=row["patient_id"],
            appointment_date=row["appointment_date"],
            appointment_time=apt_time,
            location=row.get("location", "Hospital Clinic"),
            reason=row.get("reason"),
            severity_level=row.get("severity_level", "moderate"),
            status=row.get("status", "scheduled"),
            doctor_notes=row.get("doctor_notes"),
            patient_notes=row.get("patient_notes"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            doctor_name=row.get("doctor_name"),
            patient_name=row.get("patient_name"),
        )


class AppointmentRepository(BaseRepository):

    def create(self, doctor_id: int, patient_id: int,
               appointment_date: date, appointment_time: time,
               location: str, reason: str = "",
               severity_level: str = "moderate") -> int:
        result = self.execute_write(
            """
            INSERT INTO appointments
                (doctor_id, patient_id, appointment_date, appointment_time,
                 location, reason, severity_level, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'scheduled')
            """,
            (doctor_id, patient_id, appointment_date, appointment_time,
             location, reason, severity_level),
        )
        return result["lastrowid"]

    def get_by_id(self, appt_id: int) -> Optional[Appointment]:
        row = self.execute_one(
            """
            SELECT a.*,
                   ud.full_name AS doctor_name,
                   up.full_name AS patient_name
            FROM appointments a
            JOIN users ud ON ud.id = a.doctor_id
            JOIN users up ON up.id = a.patient_id
            WHERE a.id = %s
            """,
            (appt_id,),
        )
        return Appointment.from_row(row) if row else None

    def get_for_doctor(self, doctor_id: int, upcoming_only: bool = False) -> list:
        condition = "AND a.appointment_date >= CURDATE()" if upcoming_only else ""
        rows = self.execute_query(
            f"""
            SELECT a.*,
                   ud.full_name AS doctor_name,
                   up.full_name AS patient_name
            FROM appointments a
            JOIN users ud ON ud.id = a.doctor_id
            JOIN users up ON up.id = a.patient_id
            WHERE a.doctor_id = %s {condition}
            ORDER BY a.appointment_date ASC, a.appointment_time ASC
            """,
            (doctor_id,),
        )
        return [Appointment.from_row(r) for r in rows]

    def get_for_patient(self, patient_id: int, upcoming_only: bool = False) -> list:
        condition = "AND a.appointment_date >= CURDATE()" if upcoming_only else ""
        rows = self.execute_query(
            f"""
            SELECT a.*,
                   ud.full_name AS doctor_name,
                   up.full_name AS patient_name
            FROM appointments a
            JOIN users ud ON ud.id = a.doctor_id
            JOIN users up ON up.id = a.patient_id
            WHERE a.patient_id = %s {condition}
            ORDER BY a.appointment_date ASC, a.appointment_time ASC
            """,
            (patient_id,),
        )
        return [Appointment.from_row(r) for r in rows]

    def update_status(self, appt_id: int, status: str) -> None:
        self.execute_write(
            "UPDATE appointments SET status = %s WHERE id = %s",
            (status, appt_id),
        )

    def update_notes(self, appt_id: int, doctor_notes: str = None,
                     patient_notes: str = None) -> None:
        if doctor_notes is not None:
            self.execute_write(
                "UPDATE appointments SET doctor_notes = %s WHERE id = %s",
                (doctor_notes, appt_id),
            )
        if patient_notes is not None:
            self.execute_write(
                "UPDATE appointments SET patient_notes = %s WHERE id = %s",
                (patient_notes, appt_id),
            )

    def delete(self, appt_id: int) -> None:
        self.execute_write("DELETE FROM appointments WHERE id = %s", (appt_id,))

    def count_upcoming_for_patient(self, patient_id: int) -> int:
        row = self.execute_one(
            """
            SELECT COUNT(*) AS cnt FROM appointments
            WHERE patient_id = %s AND appointment_date >= CURDATE()
            AND status = 'scheduled'
            """,
            (patient_id,),
        )
        return row["cnt"] if row else 0

    def count_for_doctor(self, doctor_id: int, status: str = None) -> int:
        condition = "AND status = %s" if status else ""
        params = (doctor_id, status) if status else (doctor_id,)
        row = self.execute_one(
            f"""
            SELECT COUNT(*) AS cnt FROM appointments
            WHERE doctor_id = %s {condition}
            """,
            params,
        )
        return row["cnt"] if row else 0

    def count_all_for_doctor(self, doctor_id: int) -> dict:
        rows = self.execute_query(
            """
            SELECT status, COUNT(*) AS count FROM appointments
            WHERE doctor_id = %s
            GROUP BY status
            """,
            (doctor_id,),
        )
        return {row["status"]: row["count"] for row in rows}
