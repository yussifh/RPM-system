"""
vitals_service.py
--------------------
Application-layer logic for patient vitals: validation, submission,
and retrieval for trend display.

Note: this service does NOT yet trigger AI risk prediction — that
integration point is added cleanly in Phase 6 once the ML models
exist. For now, submit_vitals() validates and persists a reading.
"""

from typing import Optional

from app.database.repositories.vitals_repository import VitalsRepository
from app.database.repositories.audit_log_repository import AuditLogRepository
from app.database.models import VitalsRecord
from app.utils.validators import validate_vitals_submission


class VitalsService:

    def __init__(self,
                 vitals_repo: Optional[VitalsRepository] = None,
                 audit_repo: Optional[AuditLogRepository] = None):
        self.vitals_repo = vitals_repo or VitalsRepository()
        self.audit_repo = audit_repo or AuditLogRepository()

    def submit_vitals(self, patient_id: int,
                       systolic_bp: Optional[int] = None,
                       diastolic_bp: Optional[int] = None,
                       heart_rate: Optional[int] = None,
                       glucose_level: Optional[float] = None,
                       weight_kg: Optional[float] = None,
                       temperature_c: Optional[float] = None,
                       oxygen_saturation: Optional[int] = None,
                       symptoms: Optional[str] = None,
                       notes: Optional[str] = None) -> VitalsRecord:
        """
        Validates and persists a new vitals reading. Raises
        ValidationError (caught by the UI layer) on any bad input
        before anything touches the database.
        """
        validate_vitals_submission(
            systolic_bp=systolic_bp, diastolic_bp=diastolic_bp, heart_rate=heart_rate,
            glucose_level=glucose_level, weight_kg=weight_kg,
            temperature_c=temperature_c, oxygen_saturation=oxygen_saturation,
        )

        vitals_id = self.vitals_repo.create(
            patient_id=patient_id, systolic_bp=systolic_bp, diastolic_bp=diastolic_bp,
            heart_rate=heart_rate, glucose_level=glucose_level, weight_kg=weight_kg,
            temperature_c=temperature_c, oxygen_saturation=oxygen_saturation,
            symptoms=symptoms or None, notes=notes or None,
        )

        self.audit_repo.log("VITALS_SUBMITTED", user_id=patient_id,
                             details=f"vitals_id={vitals_id}")

        return self.vitals_repo.get_by_id(vitals_id)

    def get_history(self, patient_id: int, limit: int = 30) -> list[VitalsRecord]:
        """Oldest-first, ready for direct use in a Plotly line chart's x-axis."""
        return self.vitals_repo.get_history(patient_id, limit=limit)

    def get_latest(self, patient_id: int) -> Optional[VitalsRecord]:
        return self.vitals_repo.get_latest_for_patient(patient_id)
