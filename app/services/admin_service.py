"""
admin_service.py
-------------------
Application-layer logic for the admin dashboard: user management
(view/deactivate/reactivate, patient-doctor reassignment), doctor
account provisioning, system-wide analytics, and audit log access.
"""

from typing import Optional

from app.database.models import User
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.doctor_repository import DoctorRepository
from app.database.repositories.patient_repository import PatientRepository
from app.database.repositories.alert_repository import AlertRepository
from app.database.repositories.audit_log_repository import AuditLogRepository
from app.services.auth_service import AuthService


class AdminService:

    def __init__(self,
                 user_repo: Optional[UserRepository] = None,
                 doctor_repo: Optional[DoctorRepository] = None,
                 patient_repo: Optional[PatientRepository] = None,
                 alert_repo: Optional[AlertRepository] = None,
                 audit_repo: Optional[AuditLogRepository] = None,
                 auth_service: Optional[AuthService] = None):
        self.user_repo = user_repo or UserRepository()
        self.doctor_repo = doctor_repo or DoctorRepository()
        self.patient_repo = patient_repo or PatientRepository()
        self.alert_repo = alert_repo or AlertRepository()
        self.audit_repo = audit_repo or AuditLogRepository()
        self.auth_service = auth_service or AuthService()

    # ==============================================================
    # User management
    # ==============================================================
    def list_users_by_role(self, role: str) -> list[User]:
        """Includes inactive accounts — admins need to see them to reactivate."""
        return self.user_repo.list_by_role(role, active_only=False)

    def set_user_active(self, user_id: int, is_active: bool, admin_id: int) -> None:
        self.user_repo.set_active_status(user_id, is_active)
        action = "USER_REACTIVATED" if is_active else "USER_DEACTIVATED"
        self.audit_repo.log(action, user_id=admin_id, details=f"target_user_id={user_id}")

    def reassign_patient(self, patient_user_id: int, new_doctor_id: int, admin_id: int) -> None:
        self.patient_repo.reassign_doctor(patient_user_id, new_doctor_id)
        self.audit_repo.log(
            "PATIENT_REASSIGNED", user_id=admin_id,
            details=f"patient_id={patient_user_id}, new_doctor_id={new_doctor_id}",
        )

    # ==============================================================
    # Doctor provisioning
    # ==============================================================
    def provision_doctor(self, full_name: str, email: str, password: str,
                          specialization: Optional[str], license_number: str) -> User:
        """
        Delegates straight to AuthService (Phase 4) — no duplicated
        validation/creation logic. This is the UI-facing counterpart to
        scripts/bootstrap_admin.py's one-time CLI provisioning.
        """
        return self.auth_service.register_doctor(
            full_name=full_name, email=email, password=password,
            specialization=specialization, license_number=license_number,
        )

    # ==============================================================
    # System-wide analytics
    # ==============================================================
    def get_system_stats(self) -> dict:
        return {
            "patient_count": len(self.patient_repo.list_all()),
            "doctor_count": len(self.doctor_repo.list_all()),
            "admin_count": len(self.list_users_by_role("admin")),
            "open_alerts_by_severity": self.alert_repo.count_open_by_severity_all(),
        }

    # ==============================================================
    # Audit log
    # ==============================================================
    def get_recent_audit_logs(self, limit: int = 100) -> list[dict]:
        return self.audit_repo.list_recent(limit=limit)
