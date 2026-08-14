"""
symptom_checker_service.py
---------------------------
AI-powered symptom checker that assesses whether patient symptoms
may indicate stroke, hypertension, or diabetes.

Uses a combination of:
1. Symptom-to-disease mapping (medical knowledge base)
2. Existing ML models when patient vitals are available
3. Risk scoring based on symptom severity and combinations
"""

from dataclasses import dataclass
from typing import Optional
from app.ml.risk_engine import RiskEngine
from app.database.models import Patient, VitalsRecord


@dataclass
class SymptomResult:
    disease: str
    confidence: float
    risk_level: str
    matched_symptoms: list[str]
    description: str
    recommendations: list[str]


# Symptom-to-disease mapping with weights
SYMPTOM_MAP = {
    "stroke": {
        "symptoms": {
            "sudden_numbness": 0.9,
            "sudden_weakness": 0.85,
            "facial_drooping": 0.95,
            "difficulty_speaking": 0.9,
            "confusion": 0.7,
            "trouble_walking": 0.75,
            "sudden_headache": 0.6,
            "vision_problems": 0.65,
            "dizziness": 0.5,
            "loss_of_balance": 0.6,
            "trouble_understanding": 0.7,
            "numbness_face": 0.9,
            "numbness_arm": 0.85,
            "slurred_speech": 0.92,
        },
        "description": "Stroke occurs when blood supply to part of the brain is interrupted or reduced.",
        "recommendations": [
            "Seek immediate emergency medical attention (call 112/999)",
            "Note the time symptoms started",
            "Do not drive yourself to the hospital",
            "If symptoms improve, still see a doctor immediately",
        ],
    },
    "hypertension": {
        "symptoms": {
            "headache": 0.4,
            "dizziness": 0.45,
            "blurred_vision": 0.5,
            "nosebleeds": 0.4,
            "shortness_of_breath": 0.55,
            "chest_pain": 0.6,
            "fatigue": 0.35,
            "irregular_heartbeat": 0.65,
            "pounding_in_ears": 0.6,
            "blood_in_urine": 0.5,
            "anxiety": 0.3,
            "nausea": 0.35,
            "excessive_sweating": 0.3,
            "facial_flushing": 0.4,
        },
        "description": "Hypertension (high blood pressure) is a condition where the force of blood against artery walls is consistently too high.",
        "recommendations": [
            "Monitor your blood pressure regularly",
            "Reduce salt intake in your diet",
            "Exercise regularly (at least 30 minutes daily)",
            "Maintain a healthy weight",
            "Limit alcohol consumption",
            "Manage stress through relaxation techniques",
            "Consult your doctor for proper evaluation",
        ],
    },
    "diabetes": {
        "symptoms": {
            "excessive_thirst": 0.7,
            "frequent_urination": 0.75,
            "unexplained_weight_loss": 0.65,
            "extreme_hunger": 0.6,
            "fatigue": 0.5,
            "blurred_vision": 0.5,
            "slow_healing_wounds": 0.7,
            "frequent_infections": 0.55,
            "tingling_hands_feet": 0.6,
            "dry_skin": 0.4,
            "irritability": 0.35,
            "darkened_skin": 0.55,
            "numbness": 0.45,
            "increased_appetite": 0.5,
        },
        "description": "Diabetes is a metabolic disease that causes high blood sugar. The body either doesn't make enough insulin or can't effectively use the insulin it makes.",
        "recommendations": [
            "Get a blood glucose test done",
            "Monitor your blood sugar levels regularly",
            "Follow a balanced, low-sugar diet",
            "Exercise regularly",
            "Maintain a healthy weight",
            "Stay hydrated",
            "Consult an endocrinologist for proper diagnosis",
        ],
    },
}


class SymptomCheckerService:
    """
    Assesses disease risk based on reported symptoms.
    Combines rule-based symptom matching with ML model predictions
    when patient data is available.
    """

    def __init__(self):
        self.risk_engine = RiskEngine()

    def check_symptoms(self, symptoms: list[str],
                       patient: Optional[Patient] = None,
                       vitals: Optional[VitalsRecord] = None) -> list[SymptomResult]:
        """
        Check symptoms against all three diseases and return results
        sorted by confidence (highest first).
        """
        results = []

        for disease, config in SYMPTOM_MAP.items():
            matched = []
            total_weight = 0
            matched_weight = 0

            for symptom, weight in config["symptoms"].items():
                total_weight += weight
                if symptom in symptoms:
                    matched.append(symptom)
                    matched_weight += weight

            if not matched:
                confidence = 0.0
            else:
                confidence = min(matched_weight / (total_weight * 0.3), 1.0)

            # Boost confidence if ML model also indicates risk
            ml_boost = 0.0
            if patient and vitals:
                try:
                    ml_result = self.risk_engine.predict(disease, patient, vitals)
                    ml_risk = ml_result.get("risk_score", 0)
                    ml_boost = ml_risk * 0.2
                except Exception:
                    pass

            final_confidence = min(confidence + ml_boost, 1.0)

            # Determine risk level
            if final_confidence >= 0.7:
                risk_level = "critical"
            elif final_confidence >= 0.5:
                risk_level = "high"
            elif final_confidence >= 0.3:
                risk_level = "medium"
            else:
                risk_level = "low"

            if final_confidence > 0.1:
                results.append(SymptomResult(
                    disease=disease,
                    confidence=round(final_confidence, 3),
                    risk_level=risk_level,
                    matched_symptoms=matched,
                    description=config["description"],
                    recommendations=config["recommendations"],
                ))

        results.sort(key=lambda r: r.confidence, reverse=True)
        return results

    def get_all_symptoms(self) -> dict[str, list[str]]:
        """Return all available symptoms grouped by disease."""
        all_symptoms = {}
        for disease, config in SYMPTOM_MAP.items():
            all_symptoms[disease] = list(config["symptoms"].keys())
        return all_symptoms

    @staticmethod
    def format_symptom_name(symptom: str) -> str:
        """Convert snake_case symptom to readable format."""
        return symptom.replace("_", " ").title()
