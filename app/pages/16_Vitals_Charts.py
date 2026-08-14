"""
16_Vitals_Charts.py
-------------------
Interactive vitals trend charts for patients and doctors.
Shows BP, glucose, heart rate, SpO2, and weight over time.
"""

import streamlit as st
from datetime import date, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.core.security import SessionManager
from app.database.repositories.vitals_repository import VitalsRepository
from app.database.repositories.patient_repository import PatientRepository
from app.utils.custom_css import apply_theme, profile_widget, notification_bell, page_header, vital_card

st.set_page_config(page_title="Vitals Charts", page_icon="📈", layout="wide")
apply_theme()

user = SessionManager.get_current_user()
if not user:
    st.warning("Please log in first.")
    st.stop()

profile_widget(user)
notification_bell(user)

st.markdown(page_header("📈", "Vitals Trend Charts",
            "Interactive charts showing your health metrics over time."), unsafe_allow_html=True)

vitals_repo = VitalsRepository()

# Determine patient_id
if user["role"] == "patient":
    patient_id = user["id"]
elif user["role"] in ("doctor", "admin"):
    if user["role"] == "doctor":
        from app.services.doctor_service import DoctorService
        patients = DoctorService().get_assigned_patients(user["id"])
    else:
        patient_repo = PatientRepository()
        patients = patient_repo.list_all()

    patient_map = {p.full_name: p.user_id for p in patients}
    if not patients:
        st.info("No patients available.")
        st.stop()
    selected = st.selectbox("Select Patient", list(patient_map.keys()))
    patient_id = patient_map[selected]
else:
    st.error("Access denied.")
    st.stop()

# Date range
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    days = st.selectbox("Time Range", [7, 14, 30, 60, 90], index=2)
with col2:
    start = st.date_input("From", value=date.today() - timedelta(days=days))
with col3:
    end = st.date_input("To", value=date.today())

vitals = vitals_repo.get_history_between(patient_id, start, end)

if not vitals:
    st.info("No vitals data available for the selected period.")
else:
    # Prepare data
    dates = [v.recorded_at for v in vitals]
    bp_sys = [v.systolic_bp for v in vitals if v.systolic_bp]
    bp_dia = [v.diastolic_bp for v in vitals if v.diastolic_bp]
    hr = [v.heart_rate for v in vitals if v.heart_rate]
    glucose = [float(v.glucose_level) for v in vitals if v.glucose_level]
    spo2 = [v.oxygen_saturation for v in vitals if v.oxygen_saturation]
    weight = [float(v.weight_kg) for v in vitals if v.weight_kg]

    # ── Blood Pressure Chart ──────────────────────────────────────
    if bp_sys and bp_dia:
        st.markdown("### 🩺 Blood Pressure Trend")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates[:len(bp_sys)], y=bp_sys,
            mode="lines+markers", name="Systolic",
            line=dict(color="#C73E3A", width=2),
        ))
        fig.add_trace(go.Scatter(
            x=dates[:len(bp_dia)], y=bp_dia,
            mode="lines+markers", name="Diastolic",
            line=dict(color="#2A6A9B", width=2),
        ))
        fig.add_hrect(y0=120, y1=140, fillcolor="yellow", opacity=0.1, annotation_text="Pre-Hypertension")
        fig.add_hrect(y0=140, y1=200, fillcolor="red", opacity=0.05, annotation_text="Hypertension")
        fig.update_layout(
            yaxis_title="mmHg", xaxis_title="Date",
            height=350, margin=dict(t=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Heart Rate Chart ──────────────────────────────────────────
    if hr:
        st.markdown("### ❤️ Heart Rate Trend")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates[:len(hr)], y=hr,
            mode="lines+markers", name="Heart Rate",
            line=dict(color="#B8761D", width=2),
            fill="tozeroy", fillcolor="rgba(226,166,59,0.1)",
        ))
        fig.add_hline(y=60, line_dash="dash", line_color="green", annotation_text="Normal Low")
        fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Normal High")
        fig.update_layout(
            yaxis_title="bpm", xaxis_title="Date",
            height=300, margin=dict(t=40),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Glucose Chart ─────────────────────────────────────────────
    if glucose:
        st.markdown("### 🩸 Blood Glucose Trend")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates[:len(glucose)], y=glucose,
            mode="lines+markers", name="Glucose",
            line=dict(color="#0E7A5C", width=2),
            fill="tozeroy", fillcolor="rgba(34,169,150,0.1)",
        ))
        fig.add_hrect(y0=70, y1=100, fillcolor="green", opacity=0.1, annotation_text="Normal")
        fig.add_hrect(y0=100, y1=126, fillcolor="yellow", opacity=0.1, annotation_text="Pre-Diabetic")
        fig.add_hrect(y0=126, y1=300, fillcolor="red", opacity=0.05, annotation_text="Diabetic Range")
        fig.update_layout(
            yaxis_title="mg/dL", xaxis_title="Date",
            height=350, margin=dict(t=40),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── SpO2 Chart ────────────────────────────────────────────────
    if spo2:
        st.markdown("### 💨 Oxygen Saturation (SpO2)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates[:len(spo2)], y=spo2,
            mode="lines+markers", name="SpO2",
            line=dict(color="#2A6A9B", width=2),
        ))
        fig.add_hline(y=95, line_dash="dash", line_color="red", annotation_text="Low (Seek Help)")
        fig.update_layout(
            yaxis_title="%", xaxis_title="Date",
            yaxis=dict(range=[85, 102]),
            height=300, margin=dict(t=40),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Weight Chart ──────────────────────────────────────────────
    if weight:
        st.markdown("### ⚖️ Weight Trend")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates[:len(weight)], y=weight,
            mode="lines+markers", name="Weight",
            line=dict(color="#8B5CF6", width=2),
        ))
        fig.update_layout(
            yaxis_title="kg", xaxis_title="Date",
            height=300, margin=dict(t=40),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Stats Summary ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📊 Summary Statistics")

    c1, c2, c3, c4 = st.columns(4)
    if bp_sys:
        c1.markdown(vital_card("Avg Systolic", f"{sum(bp_sys)//len(bp_sys)}", "mmHg", tone="info"), unsafe_allow_html=True)
    if hr:
        c2.markdown(vital_card("Avg Heart Rate", f"{sum(hr)//len(hr)}", "bpm"), unsafe_allow_html=True)
    if glucose:
        c3.markdown(vital_card("Avg Glucose", f"{sum(glucose)//len(glucose):.0f}", "mg/dL", tone="amber"), unsafe_allow_html=True)
    if spo2:
        c4.markdown(vital_card("Avg SpO2", f"{sum(spo2)//len(spo2)}", "%", tone="info"), unsafe_allow_html=True)

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
