"""
2_Admin_Dashboard.py
----------------------
Admin-facing dashboard: system-wide analytics, user management
(deactivate/reactivate, patient-doctor reassignment), doctor account
provisioning, and audit log viewer.
"""

import streamlit as st

from app.core.security import SessionManager
from app.core.exceptions import ValidationError, DuplicateRecordError
from app.services.admin_service import AdminService

st.set_page_config(page_title="Admin Dashboard", page_icon="🛠️", layout="wide")

user = SessionManager.require_role("admin")

admin_service = AdminService()

st.title("🛠️ Administrator Dashboard")
st.write(f"Welcome, **{user['full_name']}**.")

overview_tab, users_tab, provision_tab, audit_tab = st.tabs(
    ["📊 Overview", "👥 Users", "🩺 Provision Doctor", "📜 Audit Log"]
)

_SEVERITY_ICONS = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}

# ==================================================================
# TAB 1: Overview
# ==================================================================
with overview_tab:
    st.subheader("System-Wide Statistics")
    stats = admin_service.get_system_stats()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Patients", stats["patient_count"])
    col2.metric("Total Doctors", stats["doctor_count"])
    col3.metric("Total Admins", stats["admin_count"])

    st.subheader("Open Alerts by Severity")
    severity_counts = stats["open_alerts_by_severity"]
    if not severity_counts:
        st.info("No open alerts system-wide.")
    else:
        cols = st.columns(4)
        for i, severity in enumerate(("critical", "high", "medium", "low")):
            count = severity_counts.get(severity, 0)
            icon = _SEVERITY_ICONS[severity]
            cols[i].metric(f"{icon} {severity.title()}", count)

# ==================================================================
# TAB 2: Users
# ==================================================================
with users_tab:
    st.subheader("User Management")
    role_filter = st.selectbox("View users by role", ["patient", "doctor", "admin"])
    users = admin_service.list_users_by_role(role_filter)

    if not users:
        st.info(f"No {role_filter} accounts found.")
    else:
        for u in users:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                status = "🟢 Active" if u.is_active else "🔴 Inactive"
                col1.write(f"**{u.full_name}** ({u.email}) — {status}")
                with col2:
                    if u.is_active:
                        if st.button("Deactivate", key=f"deact_{u.id}"):
                            admin_service.set_user_active(u.id, False, user["id"])
                            st.rerun()
                    else:
                        if st.button("Reactivate", key=f"react_{u.id}"):
                            admin_service.set_user_active(u.id, True, user["id"])
                            st.rerun()

    # --- Patient-Doctor Reassignment ---
    if role_filter == "patient":
        st.subheader("Reassign Patient to a Different Doctor")
        patients = admin_service.patient_repo.list_all()
        doctors = admin_service.doctor_repo.list_all()

        if patients and doctors:
            patient_options = {p.full_name: p.user_id for p in patients}
            doctor_options = {
                f"Dr. {d.specialization or 'General'} (License {d.license_number})": d.user_id
                for d in doctors
            }
            with st.form("reassign_form"):
                selected_patient = st.selectbox("Patient", list(patient_options.keys()))
                selected_doctor = st.selectbox("New Doctor", list(doctor_options.keys()))
                reassign_submitted = st.form_submit_button("Reassign")

                if reassign_submitted:
                    admin_service.reassign_patient(
                        patient_options[selected_patient],
                        doctor_options[selected_doctor],
                        user["id"],
                    )
                    st.success("Patient reassigned successfully.")
                    st.rerun()

# ==================================================================
# TAB 3: Provision Doctor
# ==================================================================
with provision_tab:
    st.subheader("Create a New Doctor Account")
    with st.form("provision_doctor_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Temporary Password", type="password",
                                  help="At least 8 characters, including a letter and a number.")
        specialization = st.text_input("Specialization (optional)")
        license_number = st.text_input("Medical License Number")

        submitted = st.form_submit_button("Create Doctor Account")

        if submitted:
            try:
                new_doctor = admin_service.provision_doctor(
                    full_name=full_name, email=email, password=password,
                    specialization=specialization or None, license_number=license_number,
                )
                st.success(f"Doctor account created: Dr. {new_doctor.full_name} ({new_doctor.email})")
            except (ValidationError, DuplicateRecordError) as e:
                st.error(str(e))

# ==================================================================
# TAB 4: Audit Log
# ==================================================================
with audit_tab:
    st.subheader("Recent System Activity")
    logs = admin_service.get_recent_audit_logs(limit=100)

    if not logs:
        st.info("No audit log entries yet.")
    else:
        table_data = [
            {
                "Time": log["created_at"],
                "User": log.get("user_name") or "System",
                "Action": log["action"],
                "Details": log["details"],
            }
            for log in logs
        ]
        st.dataframe(table_data, use_container_width=True)

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
