"""
doctor_service.py
--------------------
Application-layer logic for the doctor-facing dashboard: assigned
patient list, per-patient overview (profile + latest risk + vitals
history), and clinical note management.

Design decision: get_patient_overview() aggregates data from four
different repositories into one call. This keeps app/pages/3_Doctor_Dashboard.py
thin — the page asks one service for "everything about this patient"
rather than orchestrating multiple repository calls itself, which would
blur the line between Presentation and Data Access layers.
"""

from typing import Optional

from app.database.models import Patient
from app.database.repositories.patient_repository import PatientRepository
from app.database.repositories.vitals_repository import VitalsRepository
from app.database.repositories.prediction_repository import PredictionRepository
from app.database.repositories.clinical_note_repository import ClinicalNoteRepository
from app.core.exceptions import ValidationError
from app.utils.date_utils import calculate_age


class DoctorService:

    def __init__(self,
                 patient_repo: Optional[PatientRepository] = None,
                 vitals_repo: Optional[VitalsRepository] = None,
                 prediction_repo: Optional[PredictionRepository] = None,
                 note_repo: Optional[ClinicalNoteRepository] = None):
        self.patient_repo = patient_repo or PatientRepository()
        self.vitals_repo = vitals_repo or VitalsRepository()
        self.prediction_repo = prediction_repo or PredictionRepository()
        self.note_repo = note_repo or ClinicalNoteRepository()

    def get_assigned_patients(self, doctor_id: int) -> list[Patient]:
        return self.patient_repo.list_by_doctor(doctor_id)

    def get_patient_overview(self, patient_id: int, vitals_limit: int = 30) -> dict:
        """
        Aggregates everything the doctor dashboard's patient detail view
        needs in one call:
            {
                "patient": Patient,
                "age": int,
                "latest_predictions": [Prediction, ...],  # one per disease
                "vitals_history": [VitalsRecord, ...],     # oldest-first
                "notes": [dict, ...],                       # newest-first, includes doctor_name
            }
        """
        patient = self.patient_repo.get_by_user_id(patient_id)
        return {
            "patient": patient,
            "age": calculate_age(patient.date_of_birth),
            "latest_predictions": self.prediction_repo.get_latest_all_diseases(patient_id),
            "vitals_history": self.vitals_repo.get_history(patient_id, limit=vitals_limit),
            "notes": self.note_repo.list_for_patient(patient_id),
        }

    def add_clinical_note(self, doctor_id: int, patient_id: int, note_text: str) -> int:
        if not note_text or not note_text.strip():
            raise ValidationError("Clinical note cannot be empty.")
        return self.note_repo.create(doctor_id, patient_id, note_text.strip())
