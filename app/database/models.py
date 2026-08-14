"""
models.py  — FIXED VERSION
Bug fix: chronic_conditions from MySQL SET column can come back
as a Python set, string, or None. All three are now handled.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class User:
    id: Optional[int]
    full_name: str
    email: str
    password_hash: str
    role: str
    phone_number: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: dict) -> "User":
        return cls(
            id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            password_hash=row["password_hash"],
            role=row["role"],
            phone_number=row.get("phone_number"),
            is_active=bool(row["is_active"]),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


@dataclass
class Doctor:
    user_id: int
    specialization: Optional[str]
    license_number: str

    @classmethod
    def from_row(cls, row: dict) -> "Doctor":
        return cls(
            user_id=row["user_id"],
            specialization=row.get("specialization"),
            license_number=row["license_number"],
        )


@dataclass
class Patient:
    user_id: int
    date_of_birth: date
    gender: str
    assigned_doctor_id: Optional[int]
    chronic_conditions: list = field(default_factory=list)
    emergency_contact: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None

    @classmethod
    def from_row(cls, row: dict) -> "Patient":
        raw = row.get("chronic_conditions")

        # ── FIX: handle set, str, list, or None ──────────────────
        if raw is None or raw == "":
            conditions = []
        elif isinstance(raw, set):
            conditions = [c for c in raw if c]
        elif isinstance(raw, list):
            conditions = [c for c in raw if c]
        elif isinstance(raw, str):
            conditions = [c.strip() for c in raw.split(",") if c.strip()]
        else:
            conditions = []

        return cls(
            user_id=row["user_id"],
            date_of_birth=row["date_of_birth"],
            gender=row["gender"],
            assigned_doctor_id=row.get("assigned_doctor_id"),
            chronic_conditions=conditions,
            emergency_contact=row.get("emergency_contact"),
            full_name=row.get("full_name"),
            email=row.get("email"),
            is_active=row.get("is_active"),
        )


@dataclass
class VitalsRecord:
    id: Optional[int]
    patient_id: int
    recorded_at: Optional[datetime]
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    glucose_level: Optional[Decimal] = None
    weight_kg: Optional[Decimal] = None
    temperature_c: Optional[Decimal] = None
    oxygen_saturation: Optional[int] = None
    symptoms: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "VitalsRecord":
        return cls(**row)


@dataclass
class Prediction:
    id: Optional[int]
    patient_id: int
    vitals_id: int
    disease_type: str
    risk_score: Decimal
    risk_level: str
    model_version: str
    predicted_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: dict) -> "Prediction":
        return cls(**row)


@dataclass
class Alert:
    id: Optional[int]
    patient_id: int
    prediction_id: int
    severity: str
    message: str
    status: str = "open"
    acknowledged_by: Optional[int] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: dict) -> "Alert":
        return cls(**row)


@dataclass
class ClinicalNote:
    id: Optional[int]
    doctor_id: int
    patient_id: int
    note: str
    created_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: dict) -> "ClinicalNote":
        return cls(**row)


@dataclass
class AuditLog:
    id: Optional[int]
    user_id: Optional[int]
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: dict) -> "AuditLog":
        return cls(**row)
