"""
doctor_schedule_repository.py
------------------------------
Data access for doctor_schedules table.
Manages doctor availability for appointment booking.
"""

from dataclasses import dataclass
from datetime import time, datetime, timedelta
from typing import Optional

from app.database.repositories.base_repository import BaseRepository


@dataclass
class DoctorSchedule:
    id: Optional[int]
    doctor_id: int
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration_min: int
    is_active: bool
    created_at: Optional[datetime]
    doctor_name: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "DoctorSchedule":
        st = row["start_time"]
        et = row["end_time"]
        if isinstance(st, timedelta):
            st = (datetime.min + st).time()
        if isinstance(et, timedelta):
            et = (datetime.min + et).time()
        return cls(
            id=row["id"],
            doctor_id=row["doctor_id"],
            day_of_week=row["day_of_week"],
            start_time=st,
            end_time=et,
            slot_duration_min=row.get("slot_duration_min", 30),
            is_active=bool(row["is_active"]),
            created_at=row.get("created_at"),
            doctor_name=row.get("doctor_name"),
        )


DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class DoctorScheduleRepository(BaseRepository):

    def set_schedule(self, doctor_id: int, day_of_week: int,
                     start_time: time, end_time: time,
                     slot_duration_min: int = 30) -> int:
        """Set or replace a doctor's schedule for a specific day."""
        # Remove existing schedule for this day
        self.execute_write(
            "DELETE FROM doctor_schedules WHERE doctor_id = %s AND day_of_week = %s",
            (doctor_id, day_of_week),
        )
        result = self.execute_write(
            """
            INSERT INTO doctor_schedules
                (doctor_id, day_of_week, start_time, end_time, slot_duration_min)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (doctor_id, day_of_week, start_time, end_time, slot_duration_min),
        )
        return result["lastrowid"]

    def get_schedule_for_doctor(self, doctor_id: int) -> list:
        rows = self.execute_query(
            """
            SELECT ds.*, ud.full_name AS doctor_name
            FROM doctor_schedules ds
            JOIN users ud ON ud.id = ds.doctor_id
            WHERE ds.doctor_id = %s AND ds.is_active = TRUE
            ORDER BY ds.day_of_week, ds.start_time
            """,
            (doctor_id,),
        )
        return [DoctorSchedule.from_row(r) for r in rows]

    def get_schedule_for_day(self, doctor_id: int, day_of_week: int) -> list:
        rows = self.execute_query(
            """
            SELECT ds.*, ud.full_name AS doctor_name
            FROM doctor_schedules ds
            JOIN users ud ON ud.id = ds.doctor_id
            WHERE ds.doctor_id = %s AND ds.day_of_week = %s AND ds.is_active = TRUE
            ORDER BY ds.start_time
            """,
            (doctor_id, day_of_week),
        )
        return [DoctorSchedule.from_row(r) for r in rows]

    def delete_schedule(self, schedule_id: int) -> None:
        self.execute_write(
            "UPDATE doctor_schedules SET is_active = FALSE WHERE id = %s",
            (schedule_id,),
        )

    def get_all_doctors_schedules(self) -> list:
        rows = self.execute_query(
            """
            SELECT ds.*, ud.full_name AS doctor_name
            FROM doctor_schedules ds
            JOIN users ud ON ud.id = ds.doctor_id
            WHERE ds.is_active = TRUE
            ORDER BY ds.doctor_id, ds.day_of_week, ds.start_time
            """
        )
        return [DoctorSchedule.from_row(r) for r in rows]
