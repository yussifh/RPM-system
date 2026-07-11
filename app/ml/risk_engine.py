"""
risk_engine.py
-----------------
Loads the three trained disease-risk models and turns a patient's
current data (demographics + latest vitals) into a risk assessment.

This is the integration point between our application's data schema
and the ML models' expected feature schemas. Per the Phase 6 design
notes: any feature our system doesn't collect (e.g., BMI, which needs
height; smoking status; cholesterol) is passed as None/NaN, and the
model's own SimpleImputer (baked into the saved Pipeline from
preprocessing.py) fills it with the training set's median/mode. This
is a documented limitation — predictions are necessarily less reliable
than a full clinical workup, since several dataset features aren't
available from our vitals collection. See README "Limitations" section.
"""

import json
import os
from typing import Optional

import joblib
import pandas as pd

from app.core.config import Config
from app.core.exceptions import ModelNotLoadedError, PredictionError
from app.database.models import Patient, VitalsRecord
from app.utils.date_utils import calculate_age

MODELS_DIR = os.path.join(os.path.dirname(__file__), "trained_models")

_SUPPORTED_DISEASES = ("stroke", "diabetes", "hypertension")


class RiskEngine:
    """
    Lazily loads each disease's trained Pipeline + metadata on first
    use and caches it for the life of this instance. Loading a joblib
    model is cheap (milliseconds) so even a cold load on every
    Streamlit rerun is not a practical performance concern.
    """

    def __init__(self):
        self._models: dict[str, object] = {}
        self._metadata: dict[str, dict] = {}

    def _load(self, disease: str) -> None:
        if disease in self._models:
            return
        model_path = os.path.join(MODELS_DIR, f"{disease}_model.joblib")
        metadata_path = os.path.join(MODELS_DIR, f"{disease}_metadata.json")
        if not os.path.exists(model_path) or not os.path.exists(metadata_path):
            raise ModelNotLoadedError(
                f"No trained model found for '{disease}'. "
                f"Run `python ml_training/train_models.py` first."
            )
        self._models[disease] = joblib.load(model_path)
        with open(metadata_path) as f:
            self._metadata[disease] = json.load(f)

    def _build_features(self, disease: str, patient: Patient,
                         vitals: Optional[VitalsRecord]) -> pd.DataFrame:
        """
        Maps whatever data our system actually has (patient demographics,
        chronic_conditions, latest vitals) onto each disease dataset's
        expected column schema. Fields we don't collect are set to None
        and imputed by the model's pipeline at inference time.
        """
        age = calculate_age(patient.date_of_birth)
        has_condition = lambda name: name in patient.chronic_conditions  # noqa: E731

        systolic = vitals.systolic_bp if vitals else None
        diastolic = vitals.diastolic_bp if vitals else None
        glucose = float(vitals.glucose_level) if (vitals and vitals.glucose_level is not None) else None
        heart_rate = vitals.heart_rate if vitals else None

        if disease == "stroke":
            row = {
                "gender": {"male": "Male", "female": "Female"}.get(patient.gender),
                "age": age,
                "hypertension": 1 if has_condition("hypertension") else 0,
                "heart_disease": None,        # not collected by our system
                "ever_married": None,         # not collected
                "work_type": None,            # not collected
                "Residence_type": None,       # not collected
                "avg_glucose_level": glucose,
                "bmi": None,                  # requires height, not collected
                "smoking_status": None,       # not collected
            }
        elif disease == "diabetes":
            row = {
                "Pregnancies": None,          # not collected
                "Glucose": glucose,
                "BloodPressure": diastolic,
                "SkinThickness": None,
                "Insulin": None,
                "BMI": None,
                "DiabetesPedigreeFunction": None,
                "Age": age,
            }
        elif disease == "hypertension":
            row = {
                "age": age,
                "sex": {"male": "M", "female": "F"}.get(patient.gender),
                "currentSmoker": None,
                "cigsPerDay": None,
                "BPMeds": None,
                "prevalentStroke": 1 if has_condition("stroke") else 0,
                "diabetes": 1 if has_condition("diabetes") else 0,
                "totChol": None,
                "sysBP": systolic,
                "diaBP": diastolic,
                "BMI": None,
                "heartRate": heart_rate,
                "glucose": glucose,
            }
        else:
            raise PredictionError(f"Unsupported disease type: {disease}")

        return pd.DataFrame([row])

    @staticmethod
    def _classify_risk_level(probability: float) -> str:
        t = Config.RISK
        if probability >= t.critical:
            return "critical"
        if probability >= t.high:
            return "high"
        if probability >= t.medium:
            return "medium"
        return "low"

    def predict(self, disease: str, patient: Patient,
                vitals: Optional[VitalsRecord]) -> dict:
        """
        Returns a dict shaped for direct use with PredictionRepository.create():
        {disease_type, risk_score, risk_level, model_version}
        """
        if disease not in _SUPPORTED_DISEASES:
            raise PredictionError(f"Unsupported disease type: {disease}")

        self._load(disease)
        model = self._models[disease]
        model_version = self._metadata[disease]["model_version"]

        features_df = self._build_features(disease, patient, vitals)

        try:
            probability = float(model.predict_proba(features_df)[0, 1])
        except Exception as e:
            raise PredictionError(f"Inference failed for {disease}: {e}") from e

        return {
            "disease_type": disease,
            "risk_score": round(probability, 4),
            "risk_level": self._classify_risk_level(probability),
            "model_version": model_version,
        }

    def predict_all(self, patient: Patient,
                     vitals: Optional[VitalsRecord]) -> list[dict]:
        """
        Runs predictions ONLY for diseases the patient is actually being
        monitored for (patient.chronic_conditions) — no point computing
        a diabetes risk score for a non-diabetic patient.
        """
        return [
            self.predict(disease, patient, vitals)
            for disease in _SUPPORTED_DISEASES
            if disease in patient.chronic_conditions
        ]
