"""
monitoring_service.py
------------------------
Thin orchestrator that composes VitalsService, RiskEngine,
PredictionRepository, and AlertService into the complete workflow:

    patient submits vitals
        -> vitals saved (VitalsService, already tested in Phase 5)
        -> AI risk assessed per chronic condition (RiskEngine)
        -> each prediction saved (PredictionRepository)
        -> high/critical predictions trigger an alert (AlertService)

Design decision: this orchestration logic deliberately lives HERE
rather than being folded into VitalsService. VitalsService's existing
Phase 5 tests stay valid and untouched, and Single Responsibility is
preserved — VitalsService only knows about vitals; this service is the
one that knows about the end-to-end monitoring workflow.
"""

from typing import Optional

from app.database.repositories.patient_repository import PatientRepository
from app.database.repositories.prediction_repository import PredictionRepository
from app.services.vitals_service import VitalsService
from app.services.alert_service import AlertService
from app.ml.risk_engine import RiskEngine


class MonitoringService:

    def __init__(self,
                 vitals_service: Optional[VitalsService] = None,
                 patient_repo: Optional[PatientRepository] = None,
                 prediction_repo: Optional[PredictionRepository] = None,
                 alert_service: Optional[AlertService] = None,
                 risk_engine: Optional[RiskEngine] = None):
        self.vitals_service = vitals_service or VitalsService()
        self.patient_repo = patient_repo or PatientRepository()
        self.prediction_repo = prediction_repo or PredictionRepository()
        self.alert_service = alert_service or AlertService()
        self.risk_engine = risk_engine or RiskEngine()

    def submit_vitals_and_assess(self, patient_id: int, **vitals_kwargs) -> dict:
        """
        Full workflow entry point used by the Patient Dashboard.

        Returns a dict:
            {
                "vitals": VitalsRecord,
                "predictions": [ {disease_type, risk_score, risk_level, alert_created}, ... ]
            }

        Note: ValidationError from vitals_service.submit_vitals() propagates
        up uncaught — the UI layer is responsible for catching it, exactly
        as it did before this service existed (Phase 5 behavior unchanged).
        """
        vitals_record = self.vitals_service.submit_vitals(patient_id=patient_id, **vitals_kwargs)

        patient = self.patient_repo.get_by_user_id(patient_id)

        predictions_summary = []
        for prediction_data in self.risk_engine.predict_all(patient, vitals_record):
            prediction_id = self.prediction_repo.create(
                patient_id=patient_id,
                vitals_id=vitals_record.id,
                disease_type=prediction_data["disease_type"],
                risk_score=prediction_data["risk_score"],
                risk_level=prediction_data["risk_level"],
                model_version=prediction_data["model_version"],
            )

            alert_id = self.alert_service.evaluate_and_create_alert(
                patient_id=patient_id,
                prediction_id=prediction_id,
                disease_type=prediction_data["disease_type"],
                risk_level=prediction_data["risk_level"],
                risk_score=prediction_data["risk_score"],
            )

            predictions_summary.append({
                **prediction_data,
                "alert_created": alert_id is not None,
            })

        return {"vitals": vitals_record, "predictions": predictions_summary}
