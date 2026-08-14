"""
monitoring_service.py — IMPROVED VERSION
Added: AI severity engine that alerts doctor immediately when
patient symptoms or vitals reach severe/critical levels.
"""

from typing import Optional

from app.database.repositories.patient_repository import PatientRepository
from app.database.repositories.prediction_repository import PredictionRepository
from app.database.repositories.message_repository import MessageRepository
from app.database.repositories.vitals_repository import VitalsRepository
from app.services.vitals_service import VitalsService
from app.services.alert_service import AlertService
from app.services.emergency_contact_service import EmergencyContactService
from app.services.email_service import EmailService
from app.ml.risk_engine import RiskEngine
from app.ml.severity_engine import SeverityEngine, SEVERITY_ORDER, SEVERITY_MODERATE


class MonitoringService:

    def __init__(self,
                 vitals_service=None, patient_repo=None,
                 prediction_repo=None, alert_service=None,
                 risk_engine=None, message_repo=None,
                 vitals_repo=None, severity_engine=None,
                 emergency_contact_service=None, email_service=None):
        self.vitals_service   = vitals_service   or VitalsService()
        self.patient_repo     = patient_repo     or PatientRepository()
        self.prediction_repo  = prediction_repo  or PredictionRepository()
        self.alert_service    = alert_service    or AlertService()
        self.risk_engine      = risk_engine      or RiskEngine()
        self.message_repo     = message_repo     or MessageRepository()
        self.vitals_repo      = vitals_repo      or VitalsRepository()
        self.severity_engine  = severity_engine  or SeverityEngine()
        self.emergency_contact_service = emergency_contact_service or EmergencyContactService()
        self.email_service    = email_service    or EmailService()

    def submit_vitals_and_assess(self, patient_id: int, **vitals_kwargs) -> dict:
        """
        Full workflow:
        1. Save vitals
        2. Run AI severity detection (NEW — immediate symptom alert)
        3. Run AI risk assessment (chronic disease prediction)
        4. Save predictions
        5. Create alerts for high/critical risks
        6. Auto-message doctor based on severity level
        """
        vitals_record = self.vitals_service.submit_vitals(
            patient_id=patient_id, **vitals_kwargs
        )

        patient = self.patient_repo.get_by_user_id(patient_id)

        # Get patient name for messages
        from app.database.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        patient_user = user_repo.get_by_id(patient_id)
        patient_name = patient_user.full_name if patient_user else f"Patient #{patient_id}"

        # Get recent history for trend analysis
        recent_history = self.vitals_repo.get_history(patient_id, limit=5)

        # ── STEP 2: AI Severity Detection ────────────────────────
        vitals_dict = {
            "systolic_bp":       vitals_kwargs.get("systolic_bp"),
            "diastolic_bp":      vitals_kwargs.get("diastolic_bp"),
            "heart_rate":        vitals_kwargs.get("heart_rate"),
            "glucose_level":     vitals_kwargs.get("glucose_level"),
            "oxygen_saturation": vitals_kwargs.get("oxygen_saturation"),
            "temperature_c":     vitals_kwargs.get("temperature_c"),
        }
        symptoms = vitals_kwargs.get("symptoms", "") or ""

        severity_report = self.severity_engine.analyse(
            vitals=vitals_dict,
            symptoms=symptoms,
            recent_history=recent_history[:-1],  # exclude the one we just saved
            patient_name=patient_name,
        )

        # ── STEP 2B: Emergency Contact Notification ──────────────
        emergency_notification_id = None
        if severity_report.overall_severity in ("critical", "severe"):
            emergency_notification_id = self.emergency_contact_service.evaluate_and_notify(
                patient_id=patient_id,
                severity_report=severity_report,
                vitals_dict=vitals_dict,
            )

        # ── STEP 3: AI Risk Assessment ───────────────────────────
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

        # ── STEP 4: Message doctor based on severity ─────────────
        if patient and patient.assigned_doctor_id:

            # PRIORITY 1: Severity engine alert (immediate if severe/critical)
            if severity_report.should_alert_doctor:
                self.message_repo.send(
                    sender_id=patient_id,
                    receiver_id=patient.assigned_doctor_id,
                    subject=severity_report.alert_subject,
                    body=severity_report.alert_body,
                )

            # PRIORITY 2: Symptoms reported (even if moderate)
            elif symptoms.strip():
                vitals_summary = self._vitals_summary(vitals_record)
                self.message_repo.send(
                    sender_id=patient_id,
                    receiver_id=patient.assigned_doctor_id,
                    subject=f"🩺 Symptom Report from {patient_name}",
                    body=(
                        f"📋 SYMPTOM REPORT\n{'='*40}\n"
                        f"Patient: {patient_name}\n\n"
                        f"🩺 SYMPTOMS:\n{symptoms.strip()}\n\n"
                        f"📊 VITALS:\n{vitals_summary}"
                    ),
                )

            # PRIORITY 3: High/Critical AI risk (chronic disease)
            if high_risk_diseases:
                risk_lines = "\n".join(
                    f"  • {d['disease_type'].title()}: "
                    f"{d['risk_level'].upper()} ({d['risk_score']:.0%})"
                    for d in high_risk_diseases
                )
                self.message_repo.send(
                    sender_id=patient_id,
                    receiver_id=patient.assigned_doctor_id,
                    subject=f"🤖 High AI Risk Alert — {patient_name}",
                    body=(
                        f"🤖 AI RISK ALERT\n{'='*40}\n"
                        f"Patient: {patient_name}\n\n"
                        f"⚠️ AI RISK RESULTS:\n{risk_lines}\n\n"
                        f"📊 VITALS:\n{self._vitals_summary(vitals_record)}\n\n"
                        f"Please review this patient's readings as soon as possible."
                    ),
                )

            # Send email for high/critical severity
            if severity_report.overall_severity in ("critical", "severe") and patient.assigned_doctor_id:
                doctor_user = user_repo.get_by_id(patient.assigned_doctor_id)
                if doctor_user and doctor_user.email:
                    self.email_service.send_alert_notification(
                        to_email=doctor_user.email,
                        patient_name=patient_name,
                        severity=severity_report.overall_severity,
                        message=severity_report.alert_body,
                        doctor_name=doctor_user.full_name,
                    )

        return {
            "vitals":          vitals_record,
            "predictions":     predictions_summary,
            "severity_report": severity_report,
            "emergency_notification_id": emergency_notification_id,
        }

    def _vitals_summary(self, vitals) -> str:
        lines = []
        if vitals.systolic_bp and vitals.diastolic_bp:
            lines.append(f"  Blood Pressure: {vitals.systolic_bp}/{vitals.diastolic_bp} mmHg")
        if vitals.heart_rate:
            lines.append(f"  Heart Rate: {vitals.heart_rate} bpm")
        if vitals.glucose_level:
            lines.append(f"  Glucose: {float(vitals.glucose_level):.1f} mg/dL")
        if vitals.oxygen_saturation:
            lines.append(f"  SpO2: {vitals.oxygen_saturation}%")
        if vitals.temperature_c:
            lines.append(f"  Temperature: {float(vitals.temperature_c):.1f}°C")
        if vitals.weight_kg:
            lines.append(f"  Weight: {float(vitals.weight_kg):.1f} kg")
        return "\n".join(lines) if lines else "  No vitals recorded."
