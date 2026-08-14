"""
test_models.py
---------------
Unit tests for database model classes — especially the Patient.from_row
chronic_conditions fix that handles set, string, list and None.
"""

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from datetime import date, datetime
from app.database.models import Patient, User, VitalsRecord


# ── Patient.from_row ──────────────────────────────────────────────
class TestPatientFromRow:

    def _base_row(self, conditions):
        return {
            "user_id": 1, "date_of_birth": date(1990,1,1),
            "gender": "male", "assigned_doctor_id": 2,
            "chronic_conditions": conditions,
            "emergency_contact": None,
        }

    def test_conditions_from_string(self):
        p = Patient.from_row(self._base_row("diabetes,hypertension"))
        assert "diabetes" in p.chronic_conditions
        assert "hypertension" in p.chronic_conditions
        assert len(p.chronic_conditions) == 2

    def test_conditions_from_set(self):
        p = Patient.from_row(self._base_row({"stroke", "diabetes"}))
        assert len(p.chronic_conditions) == 2
        assert "stroke" in p.chronic_conditions

    def test_conditions_from_list(self):
        p = Patient.from_row(self._base_row(["hypertension"]))
        assert p.chronic_conditions == ["hypertension"]

    def test_conditions_from_none(self):
        p = Patient.from_row(self._base_row(None))
        assert p.chronic_conditions == []

    def test_conditions_from_empty_string(self):
        p = Patient.from_row(self._base_row(""))
        assert p.chronic_conditions == []

    def test_full_name_from_joined_row(self):
        row = self._base_row("diabetes")
        row["full_name"] = "John Mensah"
        row["email"] = "john@example.com"
        p = Patient.from_row(row)
        assert p.full_name == "John Mensah"

    def test_missing_full_name_defaults_none(self):
        p = Patient.from_row(self._base_row("diabetes"))
        assert p.full_name is None


# ── User.from_row ─────────────────────────────────────────────────
class TestUserFromRow:

    def test_user_from_row(self):
        row = {
            "id": 1, "full_name": "Jane Doe", "email": "jane@example.com",
            "password_hash": "hashed", "role": "patient",
            "is_active": 1, "phone_number": None,
            "created_at": None, "updated_at": None,
        }
        u = User.from_row(row)
        assert u.full_name == "Jane Doe"
        assert u.role == "patient"
        assert u.is_active is True

    def test_inactive_user(self):
        row = {
            "id": 2, "full_name": "Inactive", "email": "i@example.com",
            "password_hash": "h", "role": "patient",
            "is_active": 0, "phone_number": None,
            "created_at": None, "updated_at": None,
        }
        u = User.from_row(row)
        assert u.is_active is False


# ── VitalsRecord ──────────────────────────────────────────────────
class TestVitalsRecord:

    def test_vitals_from_row(self):
        row = {
            "id": 1, "patient_id": 5,
            "recorded_at": datetime(2026,7,20,10,0),
            "systolic_bp": 135, "diastolic_bp": 85,
            "heart_rate": 78, "glucose_level": 110.0,
            "weight_kg": 72.0, "temperature_c": 36.8,
            "oxygen_saturation": 97,
            "symptoms": "mild headache", "notes": None,
        }
        v = VitalsRecord.from_row(row)
        assert v.systolic_bp == 135
        assert v.patient_id == 5
        assert v.symptoms == "mild headache"
