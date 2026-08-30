"""
12_AI_Symptom_Checker.py
------------------------
AI-powered symptom checker that assesses whether patient symptoms
may indicate stroke, hypertension, or diabetes.

Patients can:
  - Select symptoms they are experiencing
  - Get AI-powered risk assessment
  - View detailed recommendations
  - Save assessment to their history
"""

import streamlit as st
from datetime import datetime

from app.core.security import SessionManager
from app.services.symptom_checker_service import SymptomCheckerService
from app.utils.custom_css import apply_theme, profile_widget, notification_bell, page_header

st.set_page_config(page_title="AI Symptom Checker", page_icon=":material/psychology:", layout="wide")
apply_theme()

user = SessionManager.get_current_user()
if not user:
    st.warning("Please log in first.")
    st.stop()

if user["role"] not in ("patient", "doctor"):
    st.error("Access denied.")
    st.stop()

profile_widget(user)
notification_bell(user)

st.markdown(page_header(":material/psychology:", "AI Symptom Checker", "Select your symptoms and get an AI-powered risk assessment for stroke, hypertension, and diabetes."), unsafe_allow_html=True)

symptom_service = SymptomCheckerService()
all_symptoms = symptom_service.get_all_symptoms()

# ── Symptom Selection ────────────────────────────────────────────
st.markdown("### Select Your Symptoms")

col1, col2, col3 = st.columns(3)

selected_symptoms = []

with col1:
    st.markdown("#### :material/psychology: Stroke Symptoms")
    stroke_symptoms = all_symptoms.get("stroke", [])
    for symptom in stroke_symptoms:
        display_name = SymptomCheckerService.format_symptom_name(symptom)
        if st.checkbox(display_name, key=f"stroke_{symptom}"):
            selected_symptoms.append(symptom)

with col2:
    st.markdown("#### :material/favorite: Hypertension Symptoms")
    hypertension_symptoms = all_symptoms.get("hypertension", [])
    for symptom in hypertension_symptoms:
        display_name = SymptomCheckerService.format_symptom_name(symptom)
        if st.checkbox(display_name, key=f"hyper_{symptom}"):
            selected_symptoms.append(symptom)

with col3:
    st.markdown("#### :material/bloodtype: Diabetes Symptoms")
    diabetes_symptoms = all_symptoms.get("diabetes", [])
    for symptom in diabetes_symptoms:
        display_name = SymptomCheckerService.format_symptom_name(symptom)
        if st.checkbox(display_name, key=f"diab_{symptom}"):
            selected_symptoms.append(symptom)

st.markdown("---")

# ── Assessment Button ────────────────────────────────────────────
if st.button(":material/search: Get AI Assessment", width="stretch", type="primary"):
    if not selected_symptoms:
        st.warning("Please select at least one symptom to get an assessment.")
    else:
        st.markdown("### :material/bar_chart: AI Assessment Results")
        st.info(f"**Symptoms reported:** {', '.join(SymptomCheckerService.format_symptom_name(s) for s in selected_symptoms)}")

        # Get patient and vitals for ML boost if patient
        patient = None
        vitals = None
        if user["role"] == "patient":
            try:
                from app.database.repositories.patient_repository import PatientRepository
                from app.database.repositories.vitals_repository import VitalsRepository
                patient_repo = PatientRepository()
                vitals_repo = VitalsRepository()
                patient = patient_repo.get_by_user_id(user["id"])
                vitals = vitals_repo.get_latest_for_patient(user["id"])
            except Exception:
                pass

        results = symptom_service.check_symptoms(selected_symptoms, patient, vitals)

        if not results:
            st.success("No significant risk indicators detected based on the symptoms provided.")
        else:
            for result in results:
                # Risk level colors and icons
                if result.risk_level == "critical":
                    color = "#C73E3A"
                    icon = ":material/warning:"
                    bg = "#FBE9E7"
                elif result.risk_level == "high":
                    color = "#B8761D"
                    icon = ":material/warning:"
                    bg = "#FBF3E4"
                elif result.risk_level == "medium":
                    color = "#2A6A9B"
                    icon = ":material/clipboard:"
                    bg = "#E7F0F7"
                else:
                    color = "#0E7A5C"
                    icon = ":material/check_circle:"
                    bg = "#E7F4EF"

                confidence_pct = round(result.confidence * 100, 1)

                st.markdown(f"""
                <div style="background:{bg};border-left:5px solid {color};border-radius:8px;
                     padding:20px;margin:16px 0;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <h3 style="color:{color};margin:0;">
                            {icon} {result.disease.upper()} — Risk Level: {result.risk_level.upper()}
                        </h3>
                        <div style="font-size:28px;font-weight:800;color:{color};">
                            {confidence_pct}%
                        </div>
                    </div>
                    <p style="margin:10px 0 0;color:#333;">{result.description}</p>
                </div>
                """, unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Matched Symptoms ({len(result.matched_symptoms)}):**")
                    for s in result.matched_symptoms:
                        st.markdown(f"- {SymptomCheckerService.format_symptom_name(s)}")

                with c2:
                    st.markdown("**Recommendations:**")
                    for rec in result.recommendations:
                        st.markdown(f"- {rec}")

                st.markdown("---")

            # Summary
            highest = results[0]
            if highest.risk_level in ("critical", "high"):
                st.error(f"**IMPORTANT:** Based on your symptoms, you may be at **{highest.risk_level.upper()} risk** for {highest.disease.upper()}. "
                         "Please seek medical attention as soon as possible.")
            elif highest.risk_level == "medium":
                st.warning(f"**Note:** Based on your symptoms, you have a **moderate risk** for {highest.disease.upper()}. "
                           "Consider scheduling a check-up with your doctor.")
            else:
                st.success("Your symptoms suggest a **low risk** for these conditions. "
                           "However, if you are concerned, please consult your doctor.")

            # Disclaimer
            st.markdown("""
            <div style="background:#EFF3F1;border-radius:8px;padding:16px;margin-top:20px;">
                <strong>:material/warning: Medical Disclaimer:</strong> This AI symptom checker is for informational purposes only
                and is NOT a substitute for professional medical advice, diagnosis, or treatment.
                Always seek the advice of your physician or other qualified health provider
                with any questions you may have regarding a medical condition.
            </div>
            """, unsafe_allow_html=True)

elif not selected_symptoms:
    st.info("Select symptoms from the lists above and click **Get AI Assessment** to receive your risk analysis.")

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
