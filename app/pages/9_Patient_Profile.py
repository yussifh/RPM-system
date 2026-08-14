"""
9_Patient_Profile.py
---------------------
Patient profile page — personal info, medical profile,
health summary, and account security.
"""

import streamlit as st
from datetime import date, datetime
from app.core.security import SessionManager, PasswordHasher
from app.core.exceptions import ValidationError, AuthenticationError
from app.services.auth_service import AuthService
from app.services.monitoring_service import MonitoringService
from app.services.vitals_service import VitalsService
from app.database.repositories.patient_repository import PatientRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.prediction_repository import PredictionRepository
from app.database.repositories.medication_repository import MedicationRepository
from app.database.repositories.clinical_note_repository import ClinicalNoteRepository
from app.utils.custom_css import apply_theme, profile_widget, notification_bell
from app.utils.date_utils import calculate_age

st.set_page_config(page_title="My Profile", page_icon="👤", layout="wide")
apply_theme()

user = SessionManager.require_role("patient")
auth_service       = AuthService()
patient_repo       = PatientRepository()
user_repo          = UserRepository()
vitals_service     = VitalsService()
prediction_repo    = PredictionRepository()
med_repo           = MedicationRepository()
note_repo          = ClinicalNoteRepository()

patient = patient_repo.get_by_user_id(user["id"])

profile_widget(user)
notification_bell(user)

# ── Profile Header ─────────────────────────────────────────────
initials = "".join([n[0].upper() for n in user["full_name"].split()[:2]])
age = calculate_age(patient.date_of_birth)
conditions = patient.chronic_conditions or []

st.markdown(f"""
<div style="background:white;border:1px solid #DCE5E1;border-radius:14px;
     padding:28px 32px;display:flex;align-items:center;gap:24px;
     margin-bottom:20px;">
    <div style="width:72px;height:72px;border-radius:50%;background:#0E7A5C;
         color:white;display:flex;align-items:center;justify-content:center;
         font-weight:800;font-size:26px;flex-shrink:0;font-family:monospace;">
        {initials}
    </div>
    <div>
        <div style="font-size:22px;font-weight:700;color:#16242B;">
            {user['full_name']}
        </div>
        <div style="font-size:13px;color:#5F717A;margin-top:2px;">
            {user['email']} &bull; {patient.gender.title()} &bull; Age {age}
        </div>
        <div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap;">
            <span style="background:#E7F4EF;color:#0A5E46;font-size:11px;font-weight:600;
                 padding:3px 10px;border-radius:20px;">Patient</span>
            {"".join(f'<span style="background:#FBF3E4;color:#B8761D;font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;">{c.title()}</span>' for c in conditions)}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────
personal_tab, medical_tab, summary_tab, security_tab = st.tabs([
    "👤 Personal Info", "🏥 Medical Profile", "📊 Health Summary", "🔒 Account Security"
])

# ================================================================
# TAB 1: Personal Information
# ================================================================
with personal_tab:
    st.subheader("Personal Information")

    with st.form("personal_info_form"):
        c1, c2 = st.columns(2)
        with c1:
            full_name = st.text_input("Full Name", value=user["full_name"])
            email = st.text_input("Email", value=user["email"], disabled=True)
            phone = st.text_input("Phone Number",
                                   value=user.get("phone_number") or "",
                                   placeholder="e.g. +233 24 000 0000")
        with c2:
            dob = st.date_input("Date of Birth", value=patient.date_of_birth,
                                disabled=True, help="Contact admin to change")
            gender = st.text_input("Gender", value=patient.gender.title(), disabled=True)
            emergency = st.text_input("Emergency Contact",
                                       value=patient.emergency_contact or "",
                                       placeholder="e.g. Jane Mensah — +233 20 111 2222")

        if st.form_submit_button("Save Changes", use_container_width=True):
            if not full_name or len(full_name.strip()) < 2:
                st.error("Full name must be at least 2 characters.")
            else:
                try:
                    user_repo.update_profile(user["id"], full_name.strip(), phone.strip() or None)
                    patient_repo.update_emergency_contact(user["id"], emergency.strip() or None)
                    st.success("Profile updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating profile: {e}")

    st.divider()
    st.markdown("#### Account Details")
    c1, c2, c3 = st.columns(3)
    c1.metric("Member Since", user["created_at"].strftime("%d %b %Y") if user.get("created_at") else "—")
    c2.metric("Account Status", "✅ Active" if user.get("is_active", True) else "❌ Inactive")
    c3.metric("Patient ID", f"#{user['id']}")

# ================================================================
# TAB 2: Medical Profile
# ================================================================
with medical_tab:
    st.subheader("Medical Profile")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Assigned Doctor")
        if patient.assigned_doctor_id:
            try:
                doctor_user = user_repo.get_by_id(patient.assigned_doctor_id)
                from app.database.repositories.doctor_repository import DoctorRepository
                doctor_repo = DoctorRepository()
                doctor_profile = doctor_repo.get_by_user_id(patient.assigned_doctor_id)
                st.markdown(f"""
                <div style="background:white;border:1px solid #DCE5E1;border-radius:10px;
                     padding:16px;display:flex;align-items:center;gap:14px;">
                    <div style="width:44px;height:44px;border-radius:50%;background:#2A6A9B;
                         color:white;display:flex;align-items:center;justify-content:center;
                         font-weight:700;font-size:16px;font-family:monospace;">
                        {"".join(n[0].upper() for n in doctor_user.full_name.split()[:2])}
                    </div>
                    <div>
                        <div style="font-size:14px;font-weight:600;color:#16242B;">
                            {doctor_user.full_name}
                        </div>
                        <div style="font-size:12px;color:#5F717A;">
                            {doctor_profile.specialization or 'General Practice'} &bull; {doctor_profile.license_number}
                        </div>
                        <div style="font-size:11px;color:#5F717A;">
                            {doctor_user.email}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                st.info("Doctor information unavailable.")
        else:
            st.info("No doctor assigned yet. Contact an administrator.")

    with c2:
        st.markdown("#### Chronic Conditions")
        if conditions:
            for c in conditions:
                st.markdown(f"""
                <div style="background:#FBF3E4;border:1px solid #FBF3E4;border-radius:8px;
                     padding:8px 14px;margin-bottom:6px;display:flex;align-items:center;gap:8px;">
                    <span style="font-size:14px;">⚠️</span>
                    <span style="font-size:13px;font-weight:500;color:#16242B;">{c.title()}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No chronic conditions recorded.")

    st.divider()

    st.markdown("#### Clinical Notes from Doctor")
    notes = note_repo.list_for_patient(user["id"])
    if notes:
        for note in notes[:5]:
            with st.container(border=True):
                st.write(note["note"])
                st.caption(f"— Dr. {note['doctor_name']}, {note['created_at']}")
    else:
        st.info("No clinical notes yet.")

# ================================================================
# TAB 3: Health Summary
# ================================================================
with summary_tab:
    st.subheader("Health Summary")

    history = vitals_service.get_history(user["id"], limit=100)
    active_meds = med_repo.list_for_patient(user["id"], active_only=True)
    all_preds = prediction_repo.get_latest_all_diseases(user["id"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Readings", len(history))
    c2.metric("Active Medications", len(active_meds))
    c3.metric("AI Assessments", len(all_preds))
    recent_alerts = 0
    c4.metric("Open Alerts", recent_alerts)

    st.divider()

    if history:
        latest = history[0]
        st.markdown("#### Latest Vitals")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Blood Pressure",
                   f"{latest.systolic_bp}/{latest.diastolic_bp}" if latest.systolic_bp else "—",
                   help="mmHg")
        c2.metric("Heart Rate",
                   f"{latest.heart_rate} bpm" if latest.heart_rate else "—")
        c3.metric("Glucose",
                   f"{float(latest.glucose_level):.0f} mg/dL" if latest.glucose_level else "—")
        c4.metric("SpO2",
                   f"{latest.oxygen_saturation}%" if latest.oxygen_saturation else "—")
        c5.metric("Weight",
                   f"{float(latest.weight_kg):.1f} kg" if latest.weight_kg else "—")

    if all_preds:
        st.markdown("#### Latest AI Risk Assessment")
        _RISK_ICONS = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
        cols = st.columns(len(all_preds))
        for col, pred in zip(cols, all_preds):
            icon = _RISK_ICONS.get(pred.risk_level, "⚪")
            col.metric(f"{icon} {pred.disease_type.title()}",
                       pred.risk_level.upper(),
                       f"{float(pred.risk_score):.0%} probability")

    if active_meds:
        st.markdown("#### Active Medications")
        for med in active_meds:
            st.markdown(f"""
            <div style="background:white;border:1px solid #DCE5E1;border-radius:8px;
                 padding:10px 14px;margin-bottom:6px;display:flex;
                 align-items:center;gap:10px;">
                <span style="font-size:16px;">💊</span>
                <div>
                    <strong style="font-size:13px;">{med.name}</strong>
                    <span style="color:#5F717A;font-size:12px;">
                        — {med.dosage}, {med.frequency}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    if not history and not active_meds and not all_preds:
        st.info("No health data yet. Start by submitting vitals on your dashboard.")

# ================================================================
# TAB 4: Account Security
# ================================================================
with security_tab:
    st.subheader("Account Security")

    with st.form("password_form"):
        st.markdown("#### Change Password")
        current_pw = st.text_input("Current Password", type="password")
        new_pw = st.text_input("New Password", type="password",
                                help="At least 8 characters with a letter and a number")
        confirm_pw = st.text_input("Confirm New Password", type="password")

        if st.form_submit_button("Update Password", use_container_width=True):
            if not current_pw or not new_pw or not confirm_pw:
                st.error("All fields are required.")
            elif new_pw != confirm_pw:
                st.error("New passwords do not match.")
            else:
                try:
                    auth_service.change_password(user["id"], current_pw, new_pw)
                    st.success("Password updated successfully!")
                except AuthenticationError as e:
                    st.error(str(e))
                except ValidationError as e:
                    st.error(str(e))

    st.divider()
    st.markdown("#### Session")
    st.caption(f"Logged in as: {user['email']} ({user['role'].title()})")

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
