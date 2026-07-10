"""
1_Login.py
-----------
Public authentication page: Login tab + Patient Self-Registration tab.

Design decision: Doctor/Admin accounts are intentionally NOT
self-registerable here (see auth_service.py rationale). Only the
Login tab applies to those roles.
"""

import streamlit as st

from app.services.auth_service import AuthService
from app.database.repositories.doctor_repository import DoctorRepository
from app.core.security import SessionManager
from app.core.exceptions import AuthenticationError, ValidationError, DuplicateRecordError

st.set_page_config(page_title="Login", page_icon="🔐")

auth_service = AuthService()
doctor_repo = DoctorRepository()

# If already logged in, skip straight to a redirect prompt rather than
# showing the login form again.
current_user = SessionManager.get_current_user()
if current_user is not None:
    st.success(f"You're already logged in as {current_user['full_name']} ({current_user['role']}).")
    st.info("Use the sidebar to navigate to your dashboard, or log out below.")
    if st.button("Log Out"):
        SessionManager.logout()
        st.rerun()
    st.stop()


st.title("🔐 Welcome to the RPM System")

login_tab, register_tab = st.tabs(["Log In", "Patient Registration"])

# ------------------------------------------------------------------
# LOGIN TAB
# ------------------------------------------------------------------
with login_tab:
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In", use_container_width=True)

        if submitted:
            if not email or not password:
                st.warning("Please enter both email and password.")
            else:
                try:
                    user = auth_service.authenticate(email, password)
                    SessionManager.login(user)
                    st.success(f"Welcome back, {user.full_name}!")
                    st.rerun()
                except AuthenticationError as e:
                    st.error(str(e))

# ------------------------------------------------------------------
# PATIENT REGISTRATION TAB
# ------------------------------------------------------------------
with register_tab:
    st.caption(
        "Registering as a patient. Doctor and administrator accounts "
        "are provisioned by system administrators."
    )

    doctors = doctor_repo.list_all()
    doctor_options = {"— Assign later —": None}
    doctor_options.update({f"Dr. {d.specialization or 'General'} (License {d.license_number})": d.user_id
                            for d in doctors})

    with st.form("register_form"):
        full_name = st.text_input("Full Name")
        email_r = st.text_input("Email", key="reg_email")
        password_r = st.text_input("Password", type="password", key="reg_password")
        confirm_r = st.text_input("Confirm Password", type="password")

        col1, col2 = st.columns(2)
        with col1:
            dob = st.date_input("Date of Birth", min_value="1900-01-01")
        with col2:
            gender = st.selectbox("Gender", ["male", "female", "other"])

        conditions = st.multiselect(
            "Chronic Conditions Being Managed",
            ["stroke", "diabetes", "hypertension"],
        )
        chosen_doctor_label = st.selectbox("Preferred Doctor (optional)", list(doctor_options.keys()))
        phone = st.text_input("Phone Number (optional)")
        emergency_contact = st.text_input("Emergency Contact (optional)")

        register_submitted = st.form_submit_button("Create Account", use_container_width=True)

        if register_submitted:
            if password_r != confirm_r:
                st.error("Passwords do not match.")
            else:
                try:
                    user = auth_service.register_patient(
                        full_name=full_name,
                        email=email_r,
                        password=password_r,
                        date_of_birth=dob,
                        gender=gender,
                        chronic_conditions=conditions,
                        assigned_doctor_id=doctor_options[chosen_doctor_label],
                        phone_number=phone or None,
                        emergency_contact=emergency_contact or None,
                    )
                    st.success(f"Account created for {user.full_name}! You can now log in above.")
                except (ValidationError, DuplicateRecordError) as e:
                    st.error(str(e))
