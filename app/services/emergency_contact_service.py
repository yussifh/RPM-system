"""
emergency_contact_service.py
------------------------------
Business logic for emergency contact notifications.
When vitals are critical, this service notifies the patient's
emergency contact via SMS (simulated) and logs the notification.
"""

from typing import Optional
from app.database.repositories.emergency_contact_repository import EmergencyContactRepository
from app.database.repositories.patient_repository import PatientRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.audit_log_repository import AuditLogRepository
from app.services.email_service import EmailService
from app.ml.severity_engine import SeverityReport, SEVERITY_CRITICAL, SEVERITY_SEVERE


class EmergencyContactService:

    def __init__(self,
                 emerg_repo: Optional[EmergencyContactRepository] = None,
                 patient_repo: Optional[PatientRepository] = None,
                 user_repo: Optional[UserRepository] = None,
                 audit_repo: Optional[AuditLogRepository] = None,
                 email_service: Optional[EmailService] = None):
        self.emerg_repo   = emerg_repo   or EmergencyContactRepository()
        self.patient_repo = patient_repo or PatientRepository()
        self.user_repo    = user_repo    or UserRepository()
        self.audit_repo   = audit_repo   or AuditLogRepository()
        self.email_service = email_service or EmailService()

    def evaluate_and_notify(self, patient_id: int,
                             severity_report: SeverityReport,
                             vitals_dict: dict) -> Optional[int]:
        """
        Check if severity warrants emergency contact notification.
        Returns notification ID if sent, None otherwise.

        Triggers on:
          - CRITICAL severity (always)
          - SEVERE severity with specific critical flags
        """
        should_notify = False
        if severity_report.overall_severity == SEVERITY_CRITICAL:
            should_notify = True
        elif severity_report.overall_severity == SEVERITY_SEVERE:
            critical_flags = severity_report.critical_flags
            if critical_flags:
                should_notify = True

        if not should_notify:
            return None

        patient = self.patient_repo.get_by_user_id(patient_id)
        if not patient or not patient.emergency_contact:
            return None

        user = self.user_repo.get_by_id(patient_id)
        patient_name = user.full_name if user else f"Patient #{patient_id}"

        message = self._build_message(patient_name, severity_report, vitals_dict)
        vital_snapshot = self._build_vital_snapshot(vitals_dict)

        notification_id = self.emerg_repo.create(
            patient_id=patient_id,
            emergency_contact=patient.emergency_contact,
            severity=severity_report.overall_severity,
            message=message,
            vital_snapshot=vital_snapshot,
            notification_type="sms",
        )

        self.audit_repo.log(
            "EMERGENCY_CONTACT_NOTIFIED",
            user_id=patient_id,
            details=(
                f"contact={patient.emergency_contact}, "
                f"severity={severity_report.overall_severity}, "
                f"notification_id={notification_id}"
            ),
        )

        # Send email notification to patient if they have an email
        if user and user.email:
            self.email_service.send_emergency_notification(
                to_email=user.email,
                patient_name=patient_name,
                severity=severity_report.overall_severity,
                message=message,
                vital_snapshot=vital_snapshot,
            )

        return notification_id

    def get_patient_notifications(self, patient_id: int) -> list:
        return self.emerg_repo.list_for_patient(patient_id)

    def get_all_notifications(self, limit: int = 100) -> list:
        return self.emerg_repo.list_all(limit=limit)

    def get_pending_notifications(self) -> list:
        return self.emerg_repo.list_pending()

    def acknowledge_notification(self, notification_id: int) -> None:
        self.emerg_repo.acknowledge(notification_id)

    def get_notification_stats(self) -> dict:
        return self.emerg_repo.count_by_severity()

    @staticmethod
    def _build_message(patient_name: str, severity_report: SeverityReport,
                       vitals_dict: dict) -> str:
        icon = severity_report.icon
        severity = severity_report.overall_severity.upper()

        lines = [
            f"{icon} EMERGENCY ALERT — {severity}",
            "=" * 45,
            f"Patient: {patient_name}",
            f"Severity: {severity}",
            "",
            "CRITICAL FINDINGS:",
        ]

        for flag in severity_report.critical_flags:
            lines.append(f"  • {flag.parameter} ({flag.value}): {flag.message}")

        severe_flags = [f for f in severity_report.flags
                        if f.severity == "severe"]
        if severe_flags:
            lines.append("")
            lines.append("SEVERE FINDINGS:")
            for flag in severe_flags:
                lines.append(f"  • {flag.parameter} ({flag.value}): {flag.message}")

        lines.append("")
        lines.append("CURRENT VITALS:")
        if vitals_dict.get("systolic_bp") and vitals_dict.get("diastolic_bp"):
            lines.append(f"  Blood Pressure: {vitals_dict['systolic_bp']}/{vitals_dict['diastolic_bp']} mmHg")
        if vitals_dict.get("heart_rate"):
            lines.append(f"  Heart Rate: {vitals_dict['heart_rate']} bpm")
        if vitals_dict.get("glucose_level"):
            lines.append(f"  Glucose: {float(vitals_dict['glucose_level']):.0f} mg/dL")
        if vitals_dict.get("oxygen_saturation"):
            lines.append(f"  SpO2: {vitals_dict['oxygen_saturation']}%")
        if vitals_dict.get("temperature_c"):
            lines.append(f"  Temperature: {float(vitals_dict['temperature_c']):.1f}°C")

        lines.extend([
            "",
            "=" * 45,
            "This is an automated emergency notification from the",
            "Remote Patient Monitoring System.",
            "Please check on the patient immediately.",
        ])

        return "\n".join(lines)

    @staticmethod
    def _build_vital_snapshot(vitals_dict: dict) -> str:
        parts = []
        if vitals_dict.get("systolic_bp") and vitals_dict.get("diastolic_bp"):
            parts.append(f"BP: {vitals_dict['systolic_bp']}/{vitals_dict['diastolic_bp']}")
        if vitals_dict.get("heart_rate"):
            parts.append(f"HR: {vitals_dict['heart_rate']}")
        if vitals_dict.get("glucose_level"):
            parts.append(f"Glucose: {float(vitals_dict['glucose_level']):.0f}")
        if vitals_dict.get("oxygen_saturation"):
            parts.append(f"SpO2: {vitals_dict['oxygen_saturation']}")
        if vitals_dict.get("temperature_c"):
            parts.append(f"Temp: {float(vitals_dict['temperature_c']):.1f}")
        return " | ".join(parts) if parts else "N/A"
