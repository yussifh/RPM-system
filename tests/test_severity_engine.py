"""
test_severity_engine.py
------------------------
Unit tests for the AI Severity Engine.
No database or ML model required — pure logic tests.
"""

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app.ml.severity_engine import SeverityEngine, SEVERITY_NORMAL, SEVERITY_MILD, \
    SEVERITY_MODERATE, SEVERITY_SEVERE, SEVERITY_CRITICAL


@pytest.fixture
def engine():
    return SeverityEngine()


# ── Normal vitals ─────────────────────────────────────────────────
class TestNormalVitals:

    def test_all_normal_returns_normal(self, engine):
        report = engine.analyse({"systolic_bp": 120, "diastolic_bp": 80,
                                  "heart_rate": 72, "glucose_level": 95,
                                  "oxygen_saturation": 98, "temperature_c": 36.8})
        assert report.overall_severity == SEVERITY_NORMAL

    def test_no_vitals_returns_normal(self, engine):
        report = engine.analyse({})
        assert report.overall_severity == SEVERITY_NORMAL

    def test_normal_does_not_alert_doctor(self, engine):
        report = engine.analyse({"systolic_bp": 115, "diastolic_bp": 75})
        assert report.should_alert_doctor is False


# ── Blood Pressure Tests ──────────────────────────────────────────
class TestBloodPressure:

    def test_stage2_hypertension_moderate(self, engine):
        report = engine.analyse({"systolic_bp": 145})
        assert report.overall_severity == SEVERITY_MODERATE

    def test_severely_elevated_bp_severe(self, engine):
        report = engine.analyse({"systolic_bp": 165})
        assert report.overall_severity == SEVERITY_SEVERE

    def test_hypertensive_crisis_critical(self, engine):
        report = engine.analyse({"systolic_bp": 185})
        assert report.overall_severity == SEVERITY_CRITICAL

    def test_hypertensive_crisis_triggers_alert(self, engine):
        report = engine.analyse({"systolic_bp": 185})
        assert report.should_alert_doctor is True

    def test_diastolic_crisis_critical(self, engine):
        report = engine.analyse({"diastolic_bp": 125})
        assert report.overall_severity == SEVERITY_CRITICAL

    def test_hypotension_severe(self, engine):
        report = engine.analyse({"systolic_bp": 85})
        assert report.overall_severity == SEVERITY_SEVERE


# ── Glucose Tests ─────────────────────────────────────────────────
class TestGlucose:

    def test_high_glucose_moderate(self, engine):
        report = engine.analyse({"glucose_level": 200})
        assert report.overall_severity == SEVERITY_MODERATE

    def test_very_high_glucose_severe(self, engine):
        report = engine.analyse({"glucose_level": 280})
        assert report.overall_severity == SEVERITY_SEVERE

    def test_dka_level_critical(self, engine):
        report = engine.analyse({"glucose_level": 420})
        assert report.overall_severity == SEVERITY_CRITICAL

    def test_severe_hypoglycaemia_critical(self, engine):
        report = engine.analyse({"glucose_level": 45})
        assert report.overall_severity == SEVERITY_CRITICAL

    def test_mild_hypoglycaemia_severe(self, engine):
        report = engine.analyse({"glucose_level": 62})
        assert report.overall_severity == SEVERITY_SEVERE


# ── SpO2 Tests ────────────────────────────────────────────────────
class TestOxygenSaturation:

    def test_low_spo2_moderate(self, engine):
        report = engine.analyse({"oxygen_saturation": 95})
        assert report.overall_severity == SEVERITY_MODERATE

    def test_very_low_spo2_severe(self, engine):
        report = engine.analyse({"oxygen_saturation": 92})
        assert report.overall_severity == SEVERITY_SEVERE

    def test_critically_low_spo2_critical(self, engine):
        report = engine.analyse({"oxygen_saturation": 88})
        assert report.overall_severity == SEVERITY_CRITICAL


# ── Temperature Tests ─────────────────────────────────────────────
class TestTemperature:

    def test_mild_fever_moderate(self, engine):
        report = engine.analyse({"temperature_c": 38.0})
        assert report.overall_severity == SEVERITY_MODERATE

    def test_high_fever_severe(self, engine):
        report = engine.analyse({"temperature_c": 39.5})
        assert report.overall_severity == SEVERITY_SEVERE

    def test_hyperpyrexia_critical(self, engine):
        report = engine.analyse({"temperature_c": 40.5})
        assert report.overall_severity == SEVERITY_CRITICAL

    def test_hypothermia_severe(self, engine):
        report = engine.analyse({"temperature_c": 34.5})
        assert report.overall_severity == SEVERITY_SEVERE


# ── Symptom NLP Tests ─────────────────────────────────────────────
class TestSymptomAnalysis:

    def test_chest_pain_critical(self, engine):
        report = engine.analyse({}, symptoms="I have severe chest pain")
        assert report.overall_severity == SEVERITY_CRITICAL

    def test_breathing_difficulty_critical(self, engine):
        report = engine.analyse({}, symptoms="I have difficulty breathing")
        assert report.overall_severity == SEVERITY_CRITICAL

    def test_headache_moderate(self, engine):
        report = engine.analyse({}, symptoms="I have a headache")
        assert report.overall_severity == SEVERITY_MODERATE

    def test_dizziness_moderate(self, engine):
        report = engine.analyse({}, symptoms="I feel dizzy and lightheaded")
        assert report.overall_severity == SEVERITY_MODERATE

    def test_back_pain_mild(self, engine):
        report = engine.analyse({}, symptoms="I have back pain")
        assert report.overall_severity == SEVERITY_MILD

    def test_no_symptoms_no_flags(self, engine):
        report = engine.analyse({}, symptoms="")
        assert len(report.flags) == 0

    def test_palpitations_severe(self, engine):
        report = engine.analyse({}, symptoms="my heart is racing and palpitating")
        assert report.overall_severity == SEVERITY_SEVERE

    def test_blurred_vision_severe(self, engine):
        report = engine.analyse({}, symptoms="I have blurred vision")
        assert report.overall_severity == SEVERITY_SEVERE


# ── Combined Tests ────────────────────────────────────────────────
class TestCombinedAnalysis:

    def test_high_bp_plus_chest_pain_critical(self, engine):
        report = engine.analyse({"systolic_bp": 190}, symptoms="chest pain")
        assert report.overall_severity == SEVERITY_CRITICAL
        assert report.should_alert_doctor is True

    def test_alert_message_contains_patient_name(self, engine):
        report = engine.analyse({"systolic_bp": 185}, patient_name="John Mensah")
        assert "John Mensah" in report.alert_body

    def test_alert_subject_contains_severity(self, engine):
        report = engine.analyse({"systolic_bp": 185})
        assert "CRITICAL" in report.alert_subject.upper()

    def test_multiple_flags_detected(self, engine):
        report = engine.analyse({"systolic_bp": 165, "glucose_level": 290,
                                  "oxygen_saturation": 91}, symptoms="chest pain")
        assert len(report.flags) >= 3

    def test_severity_report_has_scores(self, engine):
        report = engine.analyse({"systolic_bp": 165, "glucose_level": 280})
        assert report.vitals_score > 0
        assert report.combined_score > 0
