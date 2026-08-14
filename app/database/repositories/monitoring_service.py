"""
monitoring_service.py  — IMPROVED VERSION
Added: auto-message to doctor when patient submits vitals with symptoms
or when AI risk level is high/critical.
"""

from typing import Optional

from app.database.repositories.patient_repository import PatientRepository
from app.database.repositories.prediction_repository import PredictionRepository
from app.database.repositories.message_repository import MessageRepository
from app.services.vitals_service import VitalsService
from app.services.alert_service import AlertService
from app.ml.risk_engine import RiskEngine


class MonitoringService:

    def __init__(self,
                 vitals_service: Optional[VitalsService] = None,
                 patient_repo: Optional[PatientRepository] = None,
                 prediction_repo: Optional[PredictionRepository] = None,
                 alert_service: Optional[AlertService] = None,
                 risk_engine: Optional[RiskEngine] = None,
                 message_repo: Optional[MessageRepository] = None):
        self.vitals_service = vitals_service or VitalsService()
        self.patient_repo = patient_repo or PatientRepository()
        self.prediction_repo = prediction_repo or PredictionRepository()
        self.alert_service = alert_service or AlertService()
        self.risk_engine = risk_engine or RiskEngine()
        self.message_repo = message_repo or MessageRepository()

    def submit_vitals_and_assess(self, patient_id: int, **vitals_kwargs) -> dict:
        """
        Full workflow:
        1. Save vitals
        2. Run AI risk assessment
        3. Save predictions
        4. Create alerts for high/critical risks
        5. Auto-message doctor if symptoms reported or risk is high/critical
        """
        vitals_record = self.vitals_service.submit_vitals(
            patient_id=patient_id, **vitals_kwargs
        )

        patient = self.patient_repo.get_by_user_id(patient_id)

        predictions_summary = []
        high_risk_diseases = []

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

            if prediction_data["risk_level"] in ("high", "critical"):
                high_risk_diseases.append(prediction_data)

            predictions_summary.append({
                **prediction_data,
                "alert_created": alert_id is not None,
            })

        # ── Auto-message doctor ──────────────────────────────────
        if patient and patient.assigned_doctor_id:
            symptoms = vitals_kwargs.get("symptoms", "")
            notes = vitals_kwargs.get("notes", "")

            # Get patient's full name for the message
            from app.database.repositories.user_repository import UserRepository
            user_repo = UserRepository()
            patient_user = user_repo.get_by_id(patient_id)
            patient_name = patient_user.full_name if patient_user else f"Patient #{patient_id}"

            # Case 1: Patient reported symptoms → message doctor
            if symptoms and symptoms.strip():
                vitals_summary = self._build_vitals_summary(vitals_record)
                message_body = (
                    f"📋 NEW VITALS SUBMISSION WITH SYMPTOMS\n"
                    f"{'=' * 45}\n"
                    f"Patient: {patient_name}\n"
                    f"Submitted at: {vitals_record.recorded_at}\n\n"
                    f"🩺 REPORTED SYMPTOMS:\n{symptoms.strip()}\n\n"
                    f"📊 VITALS READINGS:\n{vitals_summary}"
                )
                if notes and notes.strip():
                    message_body += f"\n\n📝 ADDITIONAL NOTES:\n{notes.strip()}"

                self.message_repo.send(
                    sender_id=patient_id,
                    receiver_id=patient.assigned_doctor_id,
                    subject=f"🩺 Symptom Report from {patient_name}",
                    body=message_body,
                )

            # Case 2: High or critical AI risk → message doctor
            if high_risk_diseases:
                risk_lines = "\n".join(
                    f"  • {d['disease_type'].title()}: "
                    f"{d['risk_level'].upper()} ({d['risk_score']:.0%} probability)"
                    for d in high_risk_diseases
                )
                vitals_summary = self._build_vitals_summary(vitals_record)
                risk_body = (
                    f"🚨 HIGH/CRITICAL RISK ALERT\n"
                    f"{'=' * 45}\n"
                    f"Patient: {patient_name}\n"
                    f"Submitted at: {vitals_record.recorded_at}\n\n"
                    f"⚠️ AI RISK ASSESSMENT:\n{risk_lines}\n\n"
                    f"📊 VITALS READINGS:\n{vitals_summary}\n\n"
                    f"Please review this patient's readings as soon as possible."
                )
                if symptoms and symptoms.strip():
                    risk_body += f"\n\n🩺 REPORTED SYMPTOMS:\n{symptoms.strip()}"

                self.message_repo.send(
                    sender_id=patient_id,
                    receiver_id=patient.assigned_doctor_id,
                    subject=f"🚨 High Risk Alert — {patient_name}",
                    body=risk_body,
                )

        return {"vitals": vitals_record, "predictions": predictions_summary}

    def _build_vitals_summary(self, vitals) -> str:
        """Build a readable vitals summary string for messages."""
        lines = []
        if vitals.systolic_bp and vitals.diastolic_bp:
            lines.append(f"  Blood Pressure: {vitals.systolic_bp}/{vitals.diastolic_bp} mmHg")
        if vitals.heart_rate:
            lines.append(f"  Heart Rate: {vitals.heart_rate} bpm")
        if vitals.glucose_level:
            lines.append(f"  Glucose Level: {float(vitals.glucose_level):.1f} mg/dL")
        if vitals.oxygen_saturation:
            lines.append(f"  Oxygen Saturation: {vitals.oxygen_saturation}%")
        if vitals.temperature_c:
            lines.append(f"  Temperature: {float(vitals.temperature_c):.1f}°C")
        if vitals.weight_kg:
            lines.append(f"  Weight: {float(vitals.weight_kg):.1f} kg")
        return "\n".join(lines) if lines else "  No vitals recorded."
