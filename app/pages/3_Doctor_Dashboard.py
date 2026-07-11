"""
3_Doctor_Dashboard.py
------------------------
Doctor-facing dashboard: open AI-risk alerts queue, assigned patient
list, and per-patient detail view (risk summary, vitals trends,
clinical notes).
"""

import streamlit as st

from app.core.security import SessionManager
from app.core.exceptions import ValidationError
from app.services.doctor_service import DoctorService
from app.services.alert_service import AlertService
from app.utils.visualizations import build_blood_pressure_chart, build_single_metric_chart

st.set_page_config(page_title="Doctor Dashboard", page_icon="🩻", layout="wide")

user = SessionManager.require_role("doctor")

doctor_service = DoctorService()
alert_service = AlertService()

st.title("🩻 Doctor Dashboard")
st.write(f"Welcome, **Dr. {user['full_name']}**.")

alerts_tab, patients_tab = st.tabs(["🚨 Alerts", "👥 My Patients"])

_RISK_ICONS = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# ==================================================================
# TAB 1: Alerts
# ==================================================================
with alerts_tab:
    st.subheader("Open Alerts")

    open_alerts = alert_service.list_open_for_doctor(user["id"])

    if not open_alerts:
        st.info("No open alerts. All caught up.")
    else:
        for alert in open_alerts:
            icon = _RISK_ICONS.get(alert["severity"], "⚪")
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"{icon} **{alert['patient_name']}** — {alert['severity'].upper()}")
                    st.write(alert["message"])
                    st.caption(f"Created: {alert['created_at']}")
                with col2:
                    if st.button("Acknowledge", key=f"ack_{alert['id']}"):
                        alert_service.acknowledge(alert["id"], user["id"])
                        st.rerun()
                    if st.button("Resolve", key=f"resolve_{alert['id']}"):
                        alert_service.resolve(alert["id"])
                        st.rerun()

# ==================================================================
# TAB 2: My Patients
# ==================================================================
with patients_tab:
    patients = doctor_service.get_assigned_patients(user["id"])

    if not patients:
        st.info("No patients currently assigned to you.")
    else:
        patient_options = {p.full_name: p.user_id for p in patients}
        selected_name = st.selectbox("Select a patient", list(patient_options.keys()))
        selected_id = patient_options[selected_name]

        overview = doctor_service.get_patient_overview(selected_id)
        patient = overview["patient"]

        st.subheader(f"{patient.full_name}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Age", overview["age"])
        col2.metric("Gender", patient.gender.title())
        col3.metric("Conditions", ", ".join(c.title() for c in patient.chronic_conditions) or "—")

        # --- Latest AI Risk Summary ---
        st.markdown("#### Latest AI Risk Assessment")
        if not overview["latest_predictions"]:
            st.caption("No AI predictions yet — patient hasn't submitted vitals.")
        else:
            pred_cols = st.columns(len(overview["latest_predictions"]))
            for col, pred in zip(pred_cols, overview["latest_predictions"]):
                icon = _RISK_ICONS.get(pred.risk_level, "⚪")
                col.metric(
                    f"{icon} {pred.disease_type.title()}",
                    f"{pred.risk_level.upper()}",
                    f"{float(pred.risk_score):.0%} probability",
                )

        # --- Vitals Trends ---
        st.markdown("#### Vitals History")
        history = overview["vitals_history"]
        if not history:
            st.caption("No vitals submitted yet.")
        else:
            bp_records = [r for r in history if r.systolic_bp is not None and r.diastolic_bp is not None]
            if bp_records:
                st.plotly_chart(build_blood_pressure_chart(bp_records), use_container_width=True)

            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                if any(r.heart_rate is not None for r in history):
                    st.plotly_chart(
                        build_single_metric_chart(history, "heart_rate", "Heart Rate", "bpm",
                                                   normal_range=(60, 100), color="#9467bd"),
                        use_container_width=True,
                    )
            with chart_col2:
                if any(r.glucose_level is not None for r in history):
                    st.plotly_chart(
                        build_single_metric_chart(history, "glucose_level", "Glucose Level", "mg/dL",
                                                    normal_range=(70, 140), color="#ff7f0e"),
                        use_container_width=True,
                    )

        # --- Clinical Notes ---
        st.markdown("#### Clinical Notes")
        with st.form(f"note_form_{selected_id}"):
            new_note = st.text_area("Add a clinical note")
            note_submitted = st.form_submit_button("Add Note")
            if note_submitted:
                try:
                    doctor_service.add_clinical_note(user["id"], selected_id, new_note)
                    st.success("Note added.")
                    st.rerun()
                except ValidationError as e:
                    st.error(str(e))

        if overview["notes"]:
            for note in overview["notes"]:
                with st.container(border=True):
                    st.write(note["note"])
                    st.caption(f"— Dr. {note['doctor_name']}, {note['created_at']}")
        else:
            st.caption("No clinical notes yet.")

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
