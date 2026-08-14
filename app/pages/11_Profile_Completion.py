"""
11_Profile_Completion.py — First-login profile verification
Patients are prompted to verify and complete their profile after first login.
"""

import streamlit as st
from app.core.security import SessionManager
from app.core.exceptions import ValidationError
from app.database.repositories.patient_repository import PatientRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.doctor_repository import DoctorRepository
from app.utils.custom_css import apply_theme, profile_widget

st.set_page_config(page_title="Complete Your Profile", page_icon="📋", layout="centered")
apply_theme()

user = SessionManager.require_role("patient")

if user["role"] != "patient":
    st.error("This page is for patients only.")
    st.stop()

patient_repo = PatientRepository()
user_repo = UserRepository()
doctor_repo = DoctorRepository()

profile_widget(user)

st.markdown("""
<div style="text-align:center;padding:24px 0 16px;">
    <div style="width:14px;height:14px;border-radius:50%;background:#0E7A5C;margin:0 auto 12px;"></div>
    <h1 style="font-size:22px;font-weight:800;color:#16242B;margin:0;">Complete Your Profile</h1>
    <p style="font-size:13px;color:#5F717A;margin:6px 0 0;">
        Please verify your information to ensure accurate health monitoring.
    </p>
</div>
""", unsafe_allow_html=True)

try:
    patient = patient_repo.get_by_user_id(user["id"])
except Exception:
    patient = None

if patient is None:
    st.error("No patient profile found. Please contact support.")
    st.stop()

# Check what needs completion
missing_fields = []
if not patient.date_of_birth:
    missing_fields.append("Date of Birth")
if not patient.gender:
    missing_fields.append("Gender")
if not patient.chronic_conditions:
    missing_fields.append("Chronic Conditions")
if not patient.emergency_contact:
    missing_fields.append("Emergency Contact")

if not missing_fields:
    st.success("Your profile is complete!")
    st.markdown("""
    <div style="text-align:center;padding:20px;">
        <p style="font-size:14px;color:#5F717A;">All required fields are filled in.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Go to Dashboard →", use_container_width=True):
        st.switch_page("pages/4_Patient_Dashboard.py")
    st.stop()

st.warning(f"Please complete the following: {', '.join(missing_fields)}")

doctors = doctor_repo.list_all()
doctor_options = {"— No Doctor —": None}
doctor_options.update({f"Dr. {d.specialization or 'General'} (Lic: {d.license_number})": d.user_id for d in doctors})

with st.form("profile_completion_form"):
    st.subheader("📋 Personal Information")

    col1, col2 = st.columns(2)
    with col1:
        dob = st.date_input(
            "Date of Birth",
            value=patient.date_of_birth if patient.date_of_birth else None,
            min_value="1900-01-01",
        )
        gender = st.selectbox(
            "Gender",
            ["male", "female", "other"],
            index=["male", "female", "other"].index(patient.gender) if patient.gender in ["male", "female", "other"] else 0,
        )
    with col2:
        emergency_contact = st.text_input(
            "Emergency Contact Name & Phone",
            value=patient.emergency_contact or "",
            placeholder="e.g. John Mensah — +233 24 000 0000",
        )
        current_doctor = patient.assigned_doctor_id
        doctor_keys = list(doctor_options.keys())
        doctor_vals = list(doctor_options.values())
        selected_idx = doctor_vals.index(current_doctor) if current_doctor in doctor_vals else 0
        chosen_doctor = st.selectbox("Assigned Doctor", doctor_keys, index=selected_idx)

    conditions = st.multiselect(
        "Chronic Conditions Being Managed",
        ["stroke", "diabetes", "hypertension"],
        default=list(patient.chronic_conditions) if patient.chronic_conditions else [],
        help="Select all conditions you are currently managing",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("Save Profile ✅", use_container_width=True)

    if submitted:
        if not conditions:
            st.error("Please select at least one chronic condition.")
        else:
            try:
                # Update patient record
                new_doctor_id = doctor_options[chosen_doctor]
                if new_doctor_id and new_doctor_id != current_doctor:
                    patient_repo.reassign_doctor(user["id"], new_doctor_id)
                patient_repo.update_conditions(user["id"], conditions)
                patient_repo.update_emergency_contact(user["id"], emergency_contact or None)

                st.success("✅ Profile updated successfully!")
                st.balloons()
                st.markdown("""
                <div style="text-align:center;padding:20px;">
                    <p style="font-size:14px;color:#5F717A;">
                        You can now access all features of the RPM System.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Go to Dashboard →", use_container_width=True):
                    st.switch_page("pages/4_Patient_Dashboard.py")

            except ValidationError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Error updating profile: {e}")

st.divider()
st.caption("⚠️ Complete profile helps your doctor provide better care.")
