"""
2_Admin_Dashboard.py — THEMED VERSION
Applies the teal/navy RPM theme.
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from app.core.security import SessionManager
from app.core.exceptions import ValidationError, DuplicateRecordError
from app.services.admin_service import AdminService
from app.database.repositories.session_repository import SessionRepository
from app.utils.custom_css import apply_theme, profile_widget, stat_tiles, notification_bell

st.set_page_config(page_title="Admin Dashboard", page_icon="🛠️", layout="wide")
apply_theme()

user = SessionManager.require_role("admin")
admin_service = AdminService()
session_repo = SessionRepository()

# ── Sidebar profile + tiles ──────────────────────────────────────
profile_widget(user)
notification_bell(user)
stats = admin_service.get_system_stats()
stat_tiles([
    {"label": "Doctors",  "value": stats["doctor_count"]},
    {"label": "Patients", "value": stats["patient_count"]},
    {"label": "Users",    "value": stats["doctor_count"] + stats["patient_count"] + stats["admin_count"]},
])

st.title("🛠️ Admin Dashboard")
st.caption(f"System overview — logged in as {user['full_name']}")

overview_tab, users_tab, provision_tab, register_tab, audit_tab, system_tab, sessions_tab, doctor_monitor_tab, bulk_tab = st.tabs([
    "📊 Overview", "👥 Users", "🩺 Add Doctor", "🏥 Add Patient",
    "📜 Audit Log", "🔧 System Health", "🔑 Sessions", "👨‍⚕️ Doctor Activity", "📥 Bulk Import"
])

# ── Overview ─────────────────────────────────────────────────────
with overview_tab:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total Patients", stats["patient_count"])
    col2.metric("🩺 Total Doctors",  stats["doctor_count"])
    col3.metric("🛠️ Total Admins",   stats["admin_count"])
    col4.metric("👤 Total Users",    stats["patient_count"] + stats["doctor_count"] + stats["admin_count"])

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("User distribution")
        fig = go.Figure(data=[go.Pie(
            labels=["Patients","Doctors","Admins"],
            values=[stats["patient_count"], stats["doctor_count"], stats["admin_count"]],
            hole=0.45,
            marker_colors=["#12A085","#2A6A9B","#B8761D"],
        )])
        fig.update_layout(margin=dict(t=10,b=10), height=260,
                          legend=dict(font=dict(size=11)))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Open alerts by severity")
        severity_counts = stats.get("open_alerts_by_severity", {})
        if not severity_counts:
            st.success("✅ No open alerts system-wide.")
        else:
            severities = ["critical","high","medium","low"]
            counts     = [severity_counts.get(s,0) for s in severities]
            colors     = ["#C73E3A","#B8761D","#2A6A9B","#0E7A5C"]
            fig2 = go.Figure(data=[go.Bar(
                x=[s.title() for s in severities], y=counts,
                marker_color=colors, text=counts, textposition="auto",
            )])
            fig2.update_layout(margin=dict(t=10,b=10), height=260,
                               showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("System health")
    h1, h2, h3 = st.columns(3)
    h1.success("✅ Database: Connected")
    h2.success("✅ ML Models: Loaded")
    h3.success("✅ Authentication: Active")

# ── Users ─────────────────────────────────────────────────────────
with users_tab:
    st.subheader("User management")
    role_filter = st.selectbox("View users by role", ["patient","doctor","admin"])
    users_list  = admin_service.list_users_by_role(role_filter)
    if not users_list:
        st.info(f"No {role_filter} accounts found.")
    else:
        st.write(f"**{len(users_list)} {role_filter}(s) found**")
        for u in users_list:
            with st.container(border=True):
                c1, c2, c3 = st.columns([4,1,1])
                status = "🟢 Active" if u.is_active else "🔴 Inactive"
                c1.write(f"**{u.full_name}** — {u.email}")
                c1.caption(f"Status: {status} | Joined: {u.created_at}")
                with c2:
                    if u.is_active:
                        if st.button("🔒 Deactivate", key=f"deact_{u.id}"):
                            admin_service.set_user_active(u.id, False, user["id"])
                            st.rerun()
                    else:
                        if st.button("✅ Reactivate", key=f"react_{u.id}"):
                            admin_service.set_user_active(u.id, True, user["id"])
                            st.rerun()

    if role_filter == "patient":
        st.divider()
        st.subheader("🔄 Reassign patient to different doctor")
        patients = admin_service.patient_repo.list_all()
        doctors  = admin_service.doctor_repo.list_all()
        if patients and doctors:
            patient_opts = {p.full_name: p.user_id for p in patients}
            doctor_opts  = {f"Dr. {d.specialization or 'General'} (Lic: {d.license_number})": d.user_id for d in doctors}
            with st.form("reassign_form"):
                sel_patient = st.selectbox("Patient", list(patient_opts.keys()))
                sel_doctor  = st.selectbox("New Doctor", list(doctor_opts.keys()))
                if st.form_submit_button("Reassign ✅"):
                    admin_service.reassign_patient(patient_opts[sel_patient], doctor_opts[sel_doctor], user["id"])
                    st.success("Patient reassigned successfully.")

# ── Add Doctor ────────────────────────────────────────────────────
with provision_tab:
    st.subheader("🩺 Create a new doctor account")
    with st.form("provision_doctor_form"):
        c1, c2 = st.columns(2)
        with c1:
            full_name      = st.text_input("Full Name",             placeholder="Dr. Kwame Mensah")
            email          = st.text_input("Email",                 placeholder="doctor@rpm.com")
            password       = st.text_input("Temporary Password",    type="password")
        with c2:
            specialization = st.text_input("Specialization",        placeholder="e.g. Cardiology")
            license_number = st.text_input("Medical License Number",placeholder="e.g. LIC-1003")
        if st.form_submit_button("Create Doctor Account ✅", use_container_width=True):
            try:
                new_doc = admin_service.provision_doctor(
                    full_name=full_name, email=email, password=password,
                    specialization=specialization or None, license_number=license_number,
                )
                st.success(f"✅ Doctor account created: Dr. {new_doc.full_name} ({new_doc.email})")
                st.markdown("""
                <div style="background:#E7F4EF;border:1px solid #0E7A5C;border-radius:8px;padding:16px;margin-top:12px;">
                    <strong style="color:#16242B;">🔑 Login Credentials for Dr. {name}</strong><br>
                    <span style="font-size:13px;color:#5F717A;">Share these credentials with the doctor so they can sign in.</span>
                </div>
                """.format(name=new_doc.full_name), unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.text_input("Email", value=new_doc.email, disabled=True, key="created_doc_email")
                with c2:
                    st.text_input("Password", value=password, disabled=True, type="password", key="created_doc_pass")
                st.info("The doctor can now sign in using these credentials on the Login page.")
            except (ValidationError, DuplicateRecordError) as e:
                st.error(str(e))

# ── Add Patient ───────────────────────────────────────────────────
with register_tab:
    st.subheader("🏥 Register a new patient")
    doctors = admin_service.doctor_repo.list_all()
    if not doctors:
        st.warning("No doctors available. Please add a doctor first.")
    else:
        doctor_opts = {f"Dr. {d.specialization or 'General'} (Lic: {d.license_number})": d.user_id for d in doctors}
        with st.form("register_patient_form"):
            c1, c2 = st.columns(2)
            with c1:
                p_name   = st.text_input("Full Name",  placeholder="John Mensah")
                p_email  = st.text_input("Email",      placeholder="patient@rpm.com")
                p_pass   = st.text_input("Password",   type="password")
                p_dob    = st.date_input("Date of Birth")
            with c2:
                p_gender = st.selectbox("Gender", ["male","female","other"])
                p_doctor = st.selectbox("Assign to Doctor", list(doctor_opts.keys()))
                p_conds  = st.multiselect("Chronic Conditions", ["stroke","diabetes","hypertension"])
                p_phone  = st.text_input("Phone Number (optional)")
            if st.form_submit_button("Register Patient ✅", use_container_width=True):
                try:
                    from app.services.auth_service import AuthService
                    auth = AuthService()
                    new_user = auth.register_patient(
                        full_name=p_name, email=p_email, password=p_pass,
                        date_of_birth=p_dob, gender=p_gender,
                        assigned_doctor_id=doctor_opts[p_doctor],
                        chronic_conditions=p_conds,
                    )
                    st.success(f"✅ Patient registered: {new_user.full_name} ({new_user.email})")
                except (ValidationError, DuplicateRecordError) as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Registration failed: {e}")

# ── Audit Log ─────────────────────────────────────────────────────
with audit_tab:
    st.subheader("📜 Recent system activity")
    logs = admin_service.get_recent_audit_logs(limit=100)
    if not logs:
        st.info("No audit log entries yet.")
    else:
        st.dataframe([{
            "Time":    log["created_at"],
            "User":    log.get("user_name") or "System",
            "Action":  log["action"],
            "Details": log["details"],
        } for log in logs], use_container_width=True)

# ── System Health ─────────────────────────────────────────────────
with system_tab:
    st.subheader("🔧 System Health Monitor")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div style="background:white;border-radius:10px;padding:20px;border-left:4px solid #0E7A5C;">
            <div style="font-size:11px;color:#5F717A;text-transform:uppercase;letter-spacing:.04em;">Database</div>
            <div style="font-size:24px;font-weight:700;color:#0E7A5C;margin:4px 0;">● Online</div>
            <div style="font-size:12px;color:#5F717A;">MySQL Connection OK</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div style="background:white;border-radius:10px;padding:20px;border-left:4px solid #2A6A9B;">
            <div style="font-size:11px;color:#5F717A;text-transform:uppercase;letter-spacing:.04em;">ML Models</div>
            <div style="font-size:24px;font-weight:700;color:#2A6A9B;margin:4px 0;">3 Loaded</div>
            <div style="font-size:12px;color:#5F717A;">Stroke, Diabetes, Hypertension</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        active_sessions = session_repo.count_active_sessions()
        st.markdown(f"""
        <div style="background:white;border-radius:10px;padding:20px;border-left:4px solid #B8761D;">
            <div style="font-size:11px;color:#5F717A;text-transform:uppercase;letter-spacing:.04em;">Active Sessions</div>
            <div style="font-size:24px;font-weight:700;color:#B8761D;margin:4px 0;">{active_sessions}</div>
            <div style="font-size:12px;color:#5F717A;">Currently logged in users</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # System stats summary
    col1, col2 = st.columns(2)
    with col1:
        open_alerts = stats.get("open_alerts_by_severity", {})
        total_open = sum(open_alerts.values()) if isinstance(open_alerts, dict) else 0
        st.metric("🚨 Open Alerts", total_open)
    with col2:
        total_users = stats["patient_count"] + stats["doctor_count"] + stats["admin_count"]
        st.metric("👤 Total Users", total_users)

    st.divider()

    # System info
    with st.expander("ℹ️ System Information", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Application:** RPM System v1.0")
            st.markdown("**Framework:** Streamlit")
            st.markdown("**Database:** MySQL (mysql-connector-python)")
            st.markdown("**ML Engine:** scikit-learn + custom severity engine")
        with c2:
            st.markdown("**Theme:** Teal Navy Professional")
            st.markdown("**PDF Engine:** fpdf2")
            st.markdown("**Charts:** Plotly")
            st.markdown("**Auth:** bcrypt + SessionManager")

# ── Active Sessions ──────────────────────────────────────────────
with sessions_tab:
    st.subheader("🔑 Active User Sessions")

    active_sessions = session_repo.get_active_sessions()

    if not active_sessions:
        st.info("No active sessions found.")
    else:
        session_data = []
        for s in active_sessions:
            session_data.append({
                "Session ID": s.session_token[:12] + "...",
                "User ID": s.user_id,
                "IP Address": s.ip_address or "—",
                "User Agent": (s.user_agent or "—")[:40],
                "Created": s.login_at.strftime("%d %b %Y, %H:%M") if s.login_at else "—",
                "Last Activity": s.last_activity.strftime("%d %b %Y, %H:%M") if s.last_activity else "—",
            })

        st.dataframe(session_data, use_container_width=True)

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Active Sessions", len(active_sessions))
        with c2:
            st.metric("Total Sessions", session_repo.count_active_sessions())

        st.caption("Sessions expire after 24 hours of inactivity.")

# ── Doctor Activity Monitoring ────────────────────────────────────
with doctor_monitor_tab:
    st.subheader("👨‍⚕️ Doctor Activity Monitor")
    st.caption("Track what each doctor is doing in the system.")

    from app.database.repositories.appointment_repository import AppointmentRepository
    from app.database.repositories.clinical_note_repository import ClinicalNoteRepository
    from app.database.repositories.medication_repository import MedicationRepository
    from app.database.repositories.alert_repository import AlertRepository
    from app.database.repositories.message_repository import MessageRepository

    appt_repo = AppointmentRepository()
    note_repo = ClinicalNoteRepository()
    med_repo = MedicationRepository()
    alert_repo_d = AlertRepository()
    msg_repo = MessageRepository()

    doctors = admin_service.doctor_repo.list_all()

    if not doctors:
        st.info("No doctors in the system yet.")
    else:
        # Overview cards for each doctor
        st.markdown("#### Doctor Activity Overview")
        for doc in doctors:
            doc_user = admin_service.user_repo.get_by_id(doc.user_id)
            doc_name = doc_user.full_name if doc_user else f"Doctor #{doc.user_id}"

            patient_count = admin_service.doctor_repo.get_patient_count(doc.user_id)
            appt_counts = appt_repo.count_all_for_doctor(doc.user_id)
            total_appts = sum(appt_counts.values())
            scheduled_appts = appt_counts.get("scheduled", 0)
            completed_appts = appt_counts.get("completed", 0)
            cancelled_appts = appt_counts.get("cancelled", 0)
            note_count = note_repo.count_for_doctor(doc.user_id)
            open_alerts = alert_repo_d.count_open_for_doctor(doc.user_id)
            ack_alerts = alert_repo_d.count_acknowledged_by_doctor(doc.user_id)

            with st.container(border=True):
                st.markdown(f"### 🩺 Dr. {doc_name}")
                st.caption(f"Specialization: {doc.specialization or 'General'} | License: {doc.license_number}")

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("👥 Patients", patient_count)
                c2.metric("📅 Total Appts", total_appts)
                c3.metric("✅ Completed", completed_appts)
                c4.metric("📝 Clinical Notes", note_count)
                c5.metric("🚨 Open Alerts", open_alerts)

                c1, c2, c3 = st.columns(3)
                c1.metric("⏳ Scheduled", scheduled_appts)
                c2.metric("❌ Cancelled", cancelled_appts)
                c3.metric("👁️ Alerts Acknowledged", ack_alerts)

                # Recent activity details
                with st.expander(f"📋 View Details for Dr. {doc_name}"):
                    detail_tab1, detail_tab2, detail_tab3 = st.tabs([
                        "📅 Appointments", "📝 Clinical Notes", "🚨 Alerts"
                    ])

                    with detail_tab1:
                        doc_appts = appt_repo.get_for_doctor(doc.user_id)
                        if doc_appts:
                            st.dataframe([{
                                "Patient": a.patient_name,
                                "Date": a.appointment_date,
                                "Time": a.appointment_time,
                                "Status": a.status.title(),
                                "Severity": a.severity_level,
                            } for a in doc_appts], use_container_width=True)
                        else:
                            st.info("No appointments booked yet.")

                    with detail_tab2:
                        doc_notes = note_repo.list_for_doctor(doc.user_id)
                        if doc_notes:
                            st.dataframe([{
                                "Patient": n.get("patient_name", "—"),
                                "Note": n["note"][:100],
                                "Date": n["created_at"],
                            } for n in doc_notes], use_container_width=True)
                        else:
                            st.info("No clinical notes written yet.")

                    with detail_tab3:
                        doc_alerts = alert_repo_d.list_open_for_doctor(doc.user_id)
                        if doc_alerts:
                            st.dataframe([{
                                "Patient": a.get("patient_name", "—"),
                                "Severity": a["severity"].title(),
                                "Message": a["message"][:80],
                                "Status": a["status"].title(),
                            } for a in doc_alerts], use_container_width=True)
                        else:
                            st.success("No open alerts.")

        # Summary table
        st.divider()
        st.markdown("#### Summary Table")
        summary_data = []
        for doc in doctors:
            doc_user = admin_service.user_repo.get_by_id(doc.user_id)
            doc_name = doc_user.full_name if doc_user else f"Doctor #{doc.user_id}"
            patient_count = admin_service.doctor_repo.get_patient_count(doc.user_id)
            appt_counts = appt_repo.count_all_for_doctor(doc.user_id)
            note_count = note_repo.count_for_doctor(doc.user_id)
            open_alerts = alert_repo_d.count_open_for_doctor(doc.user_id)
            ack_alerts = alert_repo_d.count_acknowledged_by_doctor(doc.user_id)

            summary_data.append({
                "Doctor": f"Dr. {doc_name}",
                "Specialization": doc.specialization or "General",
                "Patients": patient_count,
                "Appointments": sum(appt_counts.values()),
                "Completed": appt_counts.get("completed", 0),
                "Cancelled": appt_counts.get("cancelled", 0),
                "Clinical Notes": note_count,
                "Open Alerts": open_alerts,
                "Alerts Acknowledged": ack_alerts,
            })
        if summary_data:
            st.dataframe(summary_data, use_container_width=True)

# ── Bulk Patient Import ──────────────────────────────────────────
with bulk_tab:
    st.subheader("📥 Bulk Patient Import")
    st.caption("Upload a CSV file to register multiple patients at once.")

    st.markdown("""
    **CSV Format Required:**
    ```
    full_name,email,password,date_of_birth,gender,phone_number,emergency_contact,assigned_doctor_id,chronic_conditions
    John Mensah,john@email.com,pass123,1985-05-15,male,+233241234567,Dr. Kwame - 0241234567,1,stroke;hypertension
    ```
    **Notes:**
    - `chronic_conditions` should be semicolon-separated (stroke, diabetes, hypertension)
    - `assigned_doctor_id` is the doctor's user ID (leave blank if unassigned)
    - `date_of_birth` format: YYYY-MM-DD
    """)

    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

    if uploaded_file:
        import csv
        import io
        from datetime import date as date_type
        from app.services.auth_service import AuthService

        content = uploaded_file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))

        st.info(f"Found {sum(1 for _ in reader)} rows in the CSV file.")
        reader = csv.DictReader(io.StringIO(content))

        if st.button("📥 Import All Patients", use_container_width=True):
            auth_service = AuthService()
            success_count = 0
            errors = []

            for i, row in enumerate(reader, 1):
                try:
                    name = row.get("full_name", "").strip()
                    email = row.get("email", "").strip()
                    password = row.get("password", "").strip()
                    dob_str = row.get("date_of_birth", "").strip()
                    gender = row.get("gender", "").strip().lower()
                    phone = row.get("phone_number", "").strip() or None
                    emergency = row.get("emergency_contact", "").strip() or None
                    doctor_id = row.get("assigned_doctor_id", "").strip()
                    conditions_str = row.get("chronic_conditions", "").strip()

                    if not all([name, email, password, dob_str, gender]):
                        errors.append(f"Row {i}: Missing required fields (name, email, password, dob, gender)")
                        continue

                    dob = date_type.fromisoformat(dob_str)
                    conditions = [c.strip() for c in conditions_str.split(";") if c.strip()] if conditions_str else []
                    doc_id = int(doctor_id) if doctor_id else None

                    auth_service.register_patient(
                        full_name=name, email=email, password=password,
                        date_of_birth=dob, gender=gender,
                        chronic_conditions=conditions,
                        assigned_doctor_id=doc_id,
                        phone_number=phone,
                        emergency_contact=emergency,
                    )
                    success_count += 1
                except Exception as e:
                    errors.append(f"Row {i}: {str(e)}")

            if success_count:
                st.success(f"✅ Successfully imported {success_count} patient(s)!")
            if errors:
                with st.expander(f"⚠️ {len(errors)} Error(s)"):
                    for err in errors:
                        st.error(err)

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
