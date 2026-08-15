"""
14_Patient_Progress_Report.py
-----------------------------
Generates comprehensive patient progress reports as PDF.
Shows vitals trends, risk predictions, medication adherence,
and clinical notes over time.
"""

import streamlit as st
from datetime import date, datetime, timedelta
from io import BytesIO
from fpdf import FPDF

from app.core.security import SessionManager
from app.database.repositories.vitals_repository import VitalsRepository
from app.database.repositories.prediction_repository import PredictionRepository
from app.database.repositories.medication_repository import MedicationRepository
from app.database.repositories.appointment_repository import AppointmentRepository
from app.database.repositories.clinical_note_repository import ClinicalNoteRepository
from app.database.repositories.patient_repository import PatientRepository
from app.database.repositories.user_repository import UserRepository
from app.utils.custom_css import apply_theme, profile_widget, notification_bell, page_header

st.set_page_config(page_title="Progress Report", page_icon="📊", layout="wide")
apply_theme()

user = SessionManager.get_current_user()
if not user:
    st.warning("Please log in first.")
    st.stop()

profile_widget(user)
notification_bell(user)

st.markdown(page_header("📊", "Patient Progress Report", "Generate a comprehensive health progress report as PDF."), unsafe_allow_html=True)

# Determine patient_id
if user["role"] == "patient":
    patient_id = user["id"]
    patient_name = user["full_name"]
elif user["role"] == "doctor":
    from app.services.doctor_service import DoctorService
    doctor_service = DoctorService()
    patients = doctor_service.get_assigned_patients(user["id"])
    patient_map = {p.full_name: p.user_id for p in patients}
    if not patients:
        st.info("No patients assigned to you.")
        st.stop()
    selected = st.selectbox("Select Patient", list(patient_map.keys()))
    patient_id = patient_map[selected]
    patient_name = selected
elif user["role"] == "admin":
    patient_repo_admin = PatientRepository()
    all_patients = patient_repo_admin.list_all()
    patient_map = {p.full_name: p.user_id for p in all_patients}
    if not all_patients:
        st.info("No patients in the system.")
        st.stop()
    selected = st.selectbox("Select Patient", list(patient_map.keys()))
    patient_id = patient_map[selected]
    patient_name = selected
else:
    st.error("Access denied.")
    st.stop()

# Date range
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Report Start Date", value=date.today() - timedelta(days=30))
with col2:
    end_date = st.date_input("Report End Date", value=date.today())

# Load data
vitals_repo = VitalsRepository()
pred_repo = PredictionRepository()
med_repo = MedicationRepository()
appt_repo = AppointmentRepository()
note_repo = ClinicalNoteRepository()

vitals_history = vitals_repo.get_history_between(patient_id, start_date, end_date)
predictions = []
for disease in ["stroke", "diabetes", "hypertension"]:
    predictions.extend(pred_repo.get_history(patient_id, disease, limit=100))
active_meds = med_repo.list_for_patient(patient_id, active_only=True)
all_meds = med_repo.list_for_patient(patient_id, active_only=False)
adherence = med_repo.get_adherence_rate(patient_id, days=30)
appointments = appt_repo.get_for_patient(patient_id)

# Filter by date range
filtered_appts = [a for a in appointments if start_date <= a.appointment_date <= end_date]

# ── Preview ──────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Report Preview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Vitals Readings", len(vitals_history))
c2.metric("Active Medications", len(active_meds))
c3.metric("Appointments", len(filtered_appts))
c4.metric("Adherence Rate", f"{adherence}%")


def generate_progress_pdf(patient_name: str, start_date: date, end_date: date,
                           vitals_history: list, active_meds: list, all_meds: list,
                           filtered_appts: list, adherence: float) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_fill_color(34, 169, 150)
    pdf.rect(0, 0, 210, 35, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_y(8)
    pdf.cell(0, 10, "Remote Patient Monitoring System", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Patient Progress Report", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(42)
    pdf.set_text_color(0, 0, 0)

    # Patient info
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Patient: {patient_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Report Period: {start_date.strftime('%d %B %Y')} — {end_date.strftime('%d %B %Y')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # Summary
    pdf.set_draw_color(34, 169, 150)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Vitals Readings: {len(vitals_history)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Active Medications: {len(active_meds)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Appointments: {len(filtered_appts)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"30-Day Medication Adherence: {adherence}%", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Vitals History
    if vitals_history:
        pdf.set_draw_color(34, 169, 150)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, f"Vitals History ({len(vitals_history)} readings)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        # Table header
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(240, 240, 240)
        col_widths = [30, 25, 25, 25, 25, 25, 25]
        headers = ["Date", "BP", "HR", "Glucose", "SpO2", "Temp", "Weight"]
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for v in vitals_history[-30:]:  # Last 30 readings
            bp = f"{v.systolic_bp}/{v.diastolic_bp}" if v.systolic_bp and v.diastolic_bp else "—"
            hr = str(v.heart_rate) if v.heart_rate else "—"
            glucose = f"{float(v.glucose_level):.0f}" if v.glucose_level else "—"
            spo2 = str(v.oxygen_saturation) if v.oxygen_saturation else "—"
            temp = f"{float(v.temperature_c):.1f}" if v.temperature_c else "—"
            weight = f"{float(v.weight_kg):.1f}" if v.weight_kg else "—"
            date_str = v.recorded_at.strftime("%d %b %Y") if v.recorded_at else "—"

            row = [date_str, bp, hr, glucose, spo2, temp, weight]
            for i, val in enumerate(row):
                pdf.cell(col_widths[i], 6, val, border=1, align="C")
            pdf.ln()

    # Active Medications
    if active_meds:
        pdf.ln(4)
        pdf.set_draw_color(34, 169, 150)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, f"Active Medications ({len(active_meds)})", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        for med in active_meds:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, f"{med.name} — {med.dosage}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, f"Frequency: {med.frequency} | Route: {med.route}", new_x="LMARGIN", new_y="NEXT")
            if med.prescribed_by:
                pdf.cell(0, 5, f"Prescribed by: {med.prescribed_by}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

    # Appointments
    if filtered_appts:
        pdf.ln(4)
        pdf.set_draw_color(34, 169, 150)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, f"Appointments ({len(filtered_appts)})", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        for appt in filtered_appts:
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6, f"{appt.appointment_date} — {appt.status.title()} — {appt.location}", new_x="LMARGIN", new_y="NEXT")
            if appt.reason:
                pdf.set_font("Helvetica", "I", 9)
                pdf.cell(0, 5, f"Reason: {appt.reason}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)

    # Footer
    pdf.ln(8)
    pdf.set_draw_color(34, 169, 150)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, "Generated by RPM System — For medical use only", align="C", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())


if st.button("📥 Generate PDF Report", width="stretch", type="primary"):
    pdf_bytes = generate_progress_pdf(
        patient_name, start_date, end_date,
        vitals_history, active_meds, all_meds,
        filtered_appts, adherence
    )
    st.download_button(
        "📄 Download Progress Report PDF",
        data=pdf_bytes,
        file_name=f"progress_report_{patient_name.replace(' ', '_')}_{start_date}_{end_date}.pdf",
        mime="application/pdf",
        width="stretch",
    )
    st.success("Report generated! Click the download button above.")

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
