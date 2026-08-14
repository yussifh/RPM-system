"""
rating_repository.py
---------------------
Data access for the `doctor_ratings` table.
"""

from app.database.repositories.base_repository import BaseRepository


class RatingRepository(BaseRepository):

    def create(self, patient_user_id: int, doctor_user_id: int,
               rating: int, comment: str = None, appointment_id: int = None) -> int:
        sql = """
            INSERT INTO doctor_ratings (patient_user_id, doctor_user_id, rating, comment, appointment_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        result = self.execute_write(sql, (patient_user_id, doctor_user_id, rating, comment, appointment_id))
        return result["lastrowid"]

    def list_for_doctor(self, doctor_user_id: int) -> list[dict]:
        sql = """
            SELECT r.*, u.full_name AS patient_name
            FROM doctor_ratings r
            JOIN users u ON u.id = r.patient_user_id
            WHERE r.doctor_user_id = %s
            ORDER BY r.created_at DESC
        """
        return self.execute_query(sql, (doctor_user_id,))

    def get_average_rating(self, doctor_user_id: int) -> float:
        row = self.execute_one(
            "SELECT AVG(rating) AS avg_rating FROM doctor_ratings WHERE doctor_user_id = %s",
            (doctor_user_id,),
        )
        return round(row["avg_rating"], 1) if row and row["avg_rating"] else 0.0

    def get_total_count(self, doctor_user_id: int) -> int:
        row = self.execute_one(
            "SELECT COUNT(*) AS cnt FROM doctor_ratings WHERE doctor_user_id = %s",
            (doctor_user_id,),
        )
        return row["cnt"] if row else 0

    def has_patient_rated_doctor(self, patient_user_id: int, doctor_user_id: int,
                                  appointment_id: int = None) -> bool:
        if appointment_id:
            row = self.execute_one(
                "SELECT 1 FROM doctor_ratings WHERE patient_user_id=%s AND doctor_user_id=%s AND appointment_id=%s",
                (patient_user_id, doctor_user_id, appointment_id),
            )
        else:
            row = self.execute_one(
                "SELECT 1 FROM doctor_ratings WHERE patient_user_id=%s AND doctor_user_id=%s",
                (patient_user_id, doctor_user_id),
            )
        return row is not None

    def list_all(self) -> list[dict]:
        sql = """
            SELECT r.*, u.full_name AS patient_name, d.full_name AS doctor_name
            FROM doctor_ratings r
            JOIN users u ON u.id = r.patient_user_id
            JOIN users d ON d.id = r.doctor_user_id
            ORDER BY r.created_at DESC
        """
        return self.execute_query(sql)
