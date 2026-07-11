"""
alert_service.py
-------------------
Decides whether a given AI prediction warrants an alert, and builds
the human-readable message a doctor will see.

Kept separate from RiskEngine (pure ML inference) and PredictionRepository
(pure data access) — this is where the actual BUSINESS RULE lives:
"high or critical risk triggers an alert." Isolating that rule here
means changing alerting policy later (e.g., "also alert on medium risk
for stroke specifically") means editing one small file, not hunting
through the ML or data layers.
"""

from typing import Optional

from app.database.repositories.alert_repository import AlertRepository
from app.database.models import Alert

# Risk levels that warrant creating an alert for a doctor to review.
_ALERTABLE_LEVELS = ("high", "critical")

_DISEASE_LABELS = {
    "stroke": "Stroke",
    "diabetes": "Diabetes",
    "hypertension": "Hypertension",
}


class AlertService:

    def __init__(self, alert_repo: Optional[AlertRepository] = None):
        self.alert_repo = alert_repo or AlertRepository()

    def evaluate_and_create_alert(self, patient_id: int, prediction_id: int,
                                   disease_type: str, risk_level: str,
                                   risk_score: float) -> Optional[int]:
        """
        Creates an alert if risk_level is 'high' or 'critical'. Returns
        the new alert's id, or None if no alert was warranted.
        """
        if risk_level not in _ALERTABLE_LEVELS:
            return None

        message = self._build_message(disease_type, risk_level, risk_score)
        return self.alert_repo.create(
            patient_id=patient_id,
            prediction_id=prediction_id,
            severity=risk_level,
            message=message,
        )

    @staticmethod
    def _build_message(disease_type: str, risk_level: str, risk_score: float) -> str:
        label = _DISEASE_LABELS.get(disease_type, disease_type.title())
        urgency = "requires immediate review" if risk_level == "critical" else "should be reviewed soon"
        return (
            f"{label} risk assessed as {risk_level.upper()} "
            f"(probability: {risk_score:.0%}). This case {urgency}."
        )

    def list_open_for_doctor(self, doctor_id: int) -> list[dict]:
        return self.alert_repo.list_open_for_doctor(doctor_id)

    def acknowledge(self, alert_id: int, doctor_id: int) -> None:
        self.alert_repo.acknowledge(alert_id, doctor_id)

    def resolve(self, alert_id: int) -> None:
        self.alert_repo.resolve(alert_id)
