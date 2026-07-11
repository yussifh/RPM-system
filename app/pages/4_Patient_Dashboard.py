"""
4_Patient_Dashboard.py
-------------------------
Patient-facing dashboard: submit new vitals readings and review
personal trend history.

AI risk feedback and alerts will be added here in Phase 6 once the
ML risk_engine exists — this page is structured to make that a clean
addition rather than a rewrite.
"""

import streamlit as st

from app.core.security import SessionManager
from app.core.exceptions import ValidationError
from app.services.monitoring_service import MonitoringService
from app.services.vitals_service import VitalsService
from app.database.repositories.patient_repository import PatientRepository
from app.utils.visualizations import build_blood_pressure_chart, build_single_metric_chart

st.set_page_config(page_title="Patient Dashboard", page_icon="🧑‍⚕️", layout="wide")

user = SessionManager.require_role("patient")

monitoring_service = MonitoringService()
vitals_service = VitalsService()  # used for the read-only history tab
patient_repo = PatientRepository()

st.title("🧑‍⚕️ Patient Dashboard")
st.write(f"Welcome, **{user['full_name']}**.")

submit_tab, history_tab = st.tabs(["📝 Submit Vitals", "📈 My History & Trends"])

# ==================================================================
# TAB 1: Submit Vitals
# ==================================================================
with submit_tab:
    st.subheader("Submit a New Reading")
    st.caption("Fill in whichever readings you have available — not every field is required.")

    with st.form("vitals_form"):
        col1, col2 = st.columns(2)
        with col1:
            systolic_bp = st.number_input("Systolic BP (mmHg)", min_value=0, max_value=300,
                                           value=0, help="Leave at 0 to skip this field")
            heart_rate = st.number_input("Heart Rate (bpm)", min_value=0, max_value=250, value=0)
            weight_kg = st.number_input("Weight (kg)", min_value=0.0, max_value=350.0,
                                         value=0.0, step=0.1)
            oxygen_saturation = st.number_input("Oxygen Saturation SpO2 (%)", min_value=0,
                                                 max_value=100, value=0)
        with col2:
            diastolic_bp = st.number_input("Diastolic BP (mmHg)", min_value=0, max_value=200, value=0)
            glucose_level = st.number_input("Glucose Level (mg/dL)", min_value=0.0,
                                             max_value=600.0, value=0.0, step=0.1)
            temperature_c = st.number_input("Temperature (°C)", min_value=0.0, max_value=43.0,
                                             value=0.0, step=0.1)

        symptoms = st.text_area("Symptoms (optional)",
                                 placeholder="e.g., mild headache, dizziness, increased thirst...")
        notes = st.text_area("Additional Notes (optional)")

        submitted = st.form_submit_button("Submit Reading", use_container_width=True)

        if submitted:
            # Treat the "0 = skip" sentinel as None before sending to the service.
            # (0 is not physiologically valid for any of these fields anyway.)
            def none_if_zero(v):
                return None if v == 0 else v

            try:
                result = monitoring_service.submit_vitals_and_assess(
                    patient_id=user["id"],
                    systolic_bp=none_if_zero(systolic_bp),
                    diastolic_bp=none_if_zero(diastolic_bp),
                    heart_rate=none_if_zero(heart_rate),
                    glucose_level=none_if_zero(glucose_level),
                    weight_kg=none_if_zero(weight_kg),
                    temperature_c=none_if_zero(temperature_c),
                    oxygen_saturation=none_if_zero(oxygen_saturation),
                    symptoms=symptoms,
                    notes=notes,
                )
                st.success(f"Reading submitted successfully at {result['vitals'].recorded_at}.")

                if result["predictions"]:
                    st.subheader("AI Risk Feedback")
                    st.caption(
                        "Based on this reading and your medical history. "
                        "This is a decision-support estimate, not a diagnosis — "
                        "always follow your doctor's guidance."
                    )
                    risk_colors = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
                    for pred in result["predictions"]:
                        icon = risk_colors.get(pred["risk_level"], "⚪")
                        st.write(
                            f"{icon} **{pred['disease_type'].title()}**: "
                            f"{pred['risk_level'].upper()} risk "
                            f"({pred['risk_score']:.0%} probability)"
                        )
                        if pred["alert_created"]:
                            st.warning(
                                f"Your doctor has been alerted about this {pred['disease_type']} "
                                f"reading and will review it soon."
                            )
            except ValidationError as e:
                st.error(str(e))

# ==================================================================
# TAB 2: History & Trends
# ==================================================================
with history_tab:
    st.subheader("Your Recent History")

    history = vitals_service.get_history(user["id"], limit=30)

    if not history:
        st.info("No vitals submitted yet. Use the 'Submit Vitals' tab to add your first reading.")
    else:
        # Blood pressure chart (only if at least one record has both values)
        bp_records = [r for r in history if r.systolic_bp is not None and r.diastolic_bp is not None]
        if bp_records:
            st.plotly_chart(build_blood_pressure_chart(bp_records), use_container_width=True)

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            if any(r.heart_rate is not None for r in history):
                fig = build_single_metric_chart(history, "heart_rate", "Heart Rate", "bpm",
                                                 normal_range=(60, 100), color="#9467bd")
                st.plotly_chart(fig, use_container_width=True)
            if any(r.weight_kg is not None for r in history):
                fig = build_single_metric_chart(history, "weight_kg", "Weight", "kg",
                                                 color="#8c564b")
                st.plotly_chart(fig, use_container_width=True)
        with chart_col2:
            if any(r.glucose_level is not None for r in history):
                fig = build_single_metric_chart(history, "glucose_level", "Glucose Level", "mg/dL",
                                                 normal_range=(70, 140), color="#ff7f0e")
                st.plotly_chart(fig, use_container_width=True)
            if any(r.oxygen_saturation is not None for r in history):
                fig = build_single_metric_chart(history, "oxygen_saturation", "Oxygen Saturation", "%",
                                                 normal_range=(95, 100), color="#17becf")
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("Raw Records")
        table_data = [
            {
                "Recorded At": r.recorded_at,
                "Systolic": r.systolic_bp,
                "Diastolic": r.diastolic_bp,
                "Heart Rate": r.heart_rate,
                "Glucose": r.glucose_level,
                "Weight (kg)": r.weight_kg,
                "SpO2 (%)": r.oxygen_saturation,
                "Symptoms": r.symptoms,
            }
            for r in reversed(history)  # most recent first for the table view
        ]
        st.dataframe(table_data, use_container_width=True)

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
