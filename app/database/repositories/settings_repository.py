"""
settings_repository.py
-----------------------
Data access for the `system_settings` table.
"""

from app.database.repositories.base_repository import BaseRepository


class SettingsRepository(BaseRepository):

    DEFAULTS = {
        "clinic_name":         ("RPM Health Clinic", "Name displayed across the system"),
        "clinic_email":        ("admin@rpm.com", "Contact email"),
        "clinic_phone":        ("+233 24 000 0000", "Contact phone"),
        "vitals_threshold_bp_systolic_high":   ("140", "Systolic BP alert threshold (mmHg)"),
        "vitals_threshold_bp_diastolic_high":  ("90",  "Diastolic BP alert threshold (mmHg)"),
        "vitals_threshold_hr_high":            ("100", "Heart rate alert threshold (bpm)"),
        "vitals_threshold_hr_low":             ("50",  "Heart rate low threshold (bpm)"),
        "vitals_threshold_glucose_high":       ("200", "Glucose alert threshold (mg/dL)"),
        "vitals_threshold_glucose_low":        ("54",  "Glucose low threshold (mg/dL)"),
        "vitals_threshold_spo2_low":           ("90",  "SpO2 low threshold (%)"),
        "smtp_host":             ("", "SMTP server host"),
        "smtp_port":             ("587", "SMTP server port"),
        "smtp_user":             ("", "SMTP username"),
        "smtp_password":         ("", "SMTP password"),
        "enable_email_alerts":   ("false", "Send alerts via email"),
        "enable_sms_alerts":     ("false", "Send alerts via SMS"),
        "session_timeout_min":   ("60", "Session timeout in minutes"),
    }

    def seed_defaults(self) -> None:
        for key, (value, desc) in self.DEFAULTS.items():
            existing = self.execute_one("SELECT 1 FROM system_settings WHERE setting_key=%s", (key,))
            if not existing:
                self.execute_write(
                    "INSERT INTO system_settings (setting_key, setting_value, description) VALUES (%s,%s,%s)",
                    (key, value, desc),
                )

    def get(self, key: str) -> str | None:
        row = self.execute_one(
            "SELECT setting_value FROM system_settings WHERE setting_key=%s", (key,)
        )
        return row["setting_value"] if row else None

    def set(self, key: str, value: str, updated_by: int = None) -> None:
        self.execute_write(
            "UPDATE system_settings SET setting_value=%s, updated_by=%s WHERE setting_key=%s",
            (value, updated_by, key),
        )

    def list_all(self) -> list[dict]:
        return self.execute_query(
            "SELECT * FROM system_settings ORDER BY setting_key"
        )

    def get_many(self, keys: list[str]) -> dict[str, str]:
        if not keys:
            return {}
        placeholders = ",".join(["%s"] * len(keys))
        rows = self.execute_query(
            f"SELECT setting_key, setting_value FROM system_settings WHERE setting_key IN ({placeholders})",
            tuple(keys),
        )
        return {r["setting_key"]: r["setting_value"] for r in rows}
