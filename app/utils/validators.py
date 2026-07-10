"""
validators.py
---------------
Pure validation functions for clinical vitals data. No dependencies on
Streamlit, the database, or any other layer — just input in, either a
silent pass or a ValidationError raised.

These ranges intentionally mirror (and slightly tighten, where it aids
UX) the CHECK constraints in database/schema.sql. The DB constraints
are the last line of defense; these functions are the FIRST line,
giving patients a friendly, specific error message before anything
reaches the database.

Design decision: kept as pure functions rather than a class, since
there's no shared state — just a set of independent checks. This also
means they're trivially reusable by the ML preprocessing pipeline
(Phase 6) to reject nonsensical input before inference.
"""

from typing import Optional

from app.core.exceptions import ValidationError

# Plausible physiological ranges. (min, max) inclusive.
# These match database/schema.sql CHECK constraints for the fields that
# have them; glucose/weight/temperature don't have DB-level CHECKs
# (no ENUM-like fixed clinical consensus range as clean as BP/HR/SpO2),
# so those bounds are enforced only here at the service layer.
SYSTOLIC_BP_RANGE = (40, 300)      # mmHg
DIASTOLIC_BP_RANGE = (20, 200)     # mmHg
HEART_RATE_RANGE = (20, 250)       # bpm
GLUCOSE_RANGE = (20.0, 600.0)      # mg/dL
WEIGHT_RANGE = (2.0, 350.0)        # kg
TEMPERATURE_RANGE = (30.0, 43.0)   # Celsius
OXYGEN_SATURATION_RANGE = (0, 100) # SpO2 %


def _check_range(value, low, high, field_label: str, unit: str) -> None:
    if value is None:
        return
    if not (low <= value <= high):
        raise ValidationError(
            f"{field_label} must be between {low} and {high} {unit}. "
            f"You entered {value}. If this reading is genuinely correct, "
            f"please contact your doctor directly rather than submitting it here."
        )


def validate_systolic_bp(value: Optional[int]) -> None:
    _check_range(value, *SYSTOLIC_BP_RANGE, "Systolic blood pressure", "mmHg")


def validate_diastolic_bp(value: Optional[int]) -> None:
    _check_range(value, *DIASTOLIC_BP_RANGE, "Diastolic blood pressure", "mmHg")


def validate_heart_rate(value: Optional[int]) -> None:
    _check_range(value, *HEART_RATE_RANGE, "Heart rate", "bpm")


def validate_glucose(value: Optional[float]) -> None:
    _check_range(value, *GLUCOSE_RANGE, "Glucose level", "mg/dL")


def validate_weight(value: Optional[float]) -> None:
    _check_range(value, *WEIGHT_RANGE, "Weight", "kg")


def validate_temperature(value: Optional[float]) -> None:
    _check_range(value, *TEMPERATURE_RANGE, "Temperature", "°C")


def validate_oxygen_saturation(value: Optional[int]) -> None:
    _check_range(value, *OXYGEN_SATURATION_RANGE, "Oxygen saturation", "%")


def validate_bp_pair(systolic: Optional[int], diastolic: Optional[int]) -> None:
    """
    Cross-field check: a systolic/diastolic pair must be internally
    coherent (systolic > diastolic), not just individually in-range.
    """
    if systolic is not None and diastolic is not None and diastolic >= systolic:
        raise ValidationError(
            "Diastolic blood pressure must be lower than systolic blood pressure. "
            f"You entered systolic={systolic}, diastolic={diastolic}."
        )


def validate_vitals_submission(systolic_bp=None, diastolic_bp=None, heart_rate=None,
                                glucose_level=None, weight_kg=None, temperature_c=None,
                                oxygen_saturation=None) -> None:
    """
    Runs every individual + cross-field check for a vitals submission.
    Raises ValidationError on the FIRST violation found (fail fast with
    a specific, actionable message rather than a bundled generic one).
    """
    all_none = all(v is None for v in (
        systolic_bp, diastolic_bp, heart_rate,
        glucose_level, weight_kg, temperature_c, oxygen_saturation,
    ))
    if all_none:
        raise ValidationError(
            "Please enter at least one vital sign reading before submitting."
        )

    validate_systolic_bp(systolic_bp)
    validate_diastolic_bp(diastolic_bp)
    validate_bp_pair(systolic_bp, diastolic_bp)
    validate_heart_rate(heart_rate)
    validate_glucose(glucose_level)
    validate_weight(weight_kg)
    validate_temperature(temperature_c)
    validate_oxygen_saturation(oxygen_saturation)
