"""
4_Patient_Dashboard.py — THEMED VERSION
"""

import io, streamlit as st
from datetime import datetime
from app.core.security import SessionManager
from app.core.exceptions import ValidationError
from app.services.monitoring_service import MonitoringService
from app.services.vitals_service import VitalsService
from app.services.health_score_service import HealthScoreService
from app.database.repositories.patient_repository import PatientRepository
from app.database.repositories.prediction_repository import PredictionRepository
from app.database.repositories.medication_repository import MedicationRepository
from app.database.repositories.consent_repository import ConsentRepository
from app.database.repositories.alert_repository import AlertRepository
from app.database.repositories.appointment_repository import AppointmentRepository
from app.utils.visualizations import build_blood_pressure_chart, build_single_metric_chart
from app.utils.custom_css import apply_theme, profile_widget, notification_bell, page_header, vital_card

st.set_page_config(page_title="Patient Dashboard", page_icon="🧑‍⚕️", layout="wide")
apply_theme()

user = SessionManager.require_role("patient")
monitoring_service = MonitoringService()
vitals_service     = VitalsService()
patient_repo       = PatientRepository()
prediction_repo    = PredictionRepository()
medication_repo    = MedicationRepository()
consent_repo       = ConsentRepository()
alert_repo         = AlertRepository()
appt_repo          = AppointmentRepository()
health_score_svc   = HealthScoreService()

# ── Consent Check ─────────────────────────────────────────────────
if not consent_repo.has_consent(user["id"]):
    st.markdown("""
    <div style="text-align:center;padding:24px 0 16px;">
        <div style="width:14px;height:14px;border-radius:50%;background:#B8761D;margin:0 auto 12px;"></div>
        <h1 style="font-size:22px;font-weight:800;color:#16242B;margin:0;">Patient Consent Required</h1>
        <p style="font-size:13px;color:#5F717A;margin:6px 0 0;">
            Before you can use the RPM System, please review and accept the monitoring consent.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("""
        ### Remote Patient Monitoring — Informed Consent

        By agreeing to this consent, you acknowledge and agree to the following:

        **1. Purpose of Monitoring**
        This system collects your vital signs (blood pressure, heart rate, glucose, SpO2, temperature, weight)
        and uses AI to assess your risk for stroke, diabetes, and hypertension.

        **2. Data Collection**
        Your health data is stored securely in our database and is accessible only to you and your
        assigned healthcare provider.

        **3. AI Risk Assessment**
        The system uses machine learning models to predict health risks. These predictions are
        decision-support tools and do NOT replace professional medical advice.

        **4. Emergency Notifications**
        In case of critical health readings, your emergency contact may be notified automatically.

        **5. Data Privacy**
        Your data will not be shared with third parties without your explicit consent.
        You may request data deletion at any time.

        **6. Limitations**
        This system is for academic demonstration purposes. It is not a certified medical device.
        Always consult a qualified healthcare provider for medical decisions.
        """)

        consent_text = st.checkbox(
            "I have read and understood the above terms. I consent to remote health monitoring.",
            key="consent_checkbox"
        )

        if st.button("✅ Submit Consent", use_container_width=True):
            if consent_text:
                consent_repo.grant_consent(
                    patient_id=user["id"],
                    consent_text="Patient consented to remote monitoring via web interface.",
                )
                st.success("✅ Consent recorded. Redirecting to your dashboard...")
                st.rerun()
            else:
                st.error("Please check the consent checkbox to proceed.")

    st.stop()

# ── Sidebar ──────────────────────────────────────────────────────
profile_widget(user)
notification_bell(user)
st.sidebar.markdown("""
<div style="padding: 8px 16px;">
  <div style="font-size:9px;font-weight:700;text-transform:uppercase;
       letter-spacing:.05em;color:rgba(255,255,255,0.4);margin-bottom:6px;">My Health</div>
</div>
""", unsafe_allow_html=True)

st.markdown(page_header("🧑‍⚕️", "Patient Dashboard", f"Welcome back, {user['full_name']}"), unsafe_allow_html=True)

_RISK_COLORS = {"low":"🟢","medium":"🟡","high":"🟠","critical":"🔴"}

health_tab, submit_tab, history_tab, risk_tab, report_tab, vitals_chart_tab, timeline_tab = st.tabs([
    "🏥 Health Score", "📝 Submit Vitals", "📈 My History", "🤖 AI Risk History",
    "📄 Download Report", "📊 Vitals Overview", "📅 Health Timeline"
])

# ── Submit Vitals ─────────────────────────────────────────────────
with submit_tab:
    st.subheader("Submit a new reading")
    with st.form("vitals_form"):
        c1, c2 = st.columns(2)
        with c1:
            systolic_bp        = st.number_input("Systolic BP (mmHg)",     min_value=0, max_value=300, value=0)
            heart_rate         = st.number_input("Heart Rate (bpm)",        min_value=0, max_value=250, value=0)
            weight_kg          = st.number_input("Weight (kg)",             min_value=0.0, max_value=350.0, value=0.0, step=0.1)
            oxygen_saturation  = st.number_input("Oxygen Saturation (%)",   min_value=0, max_value=100, value=0)
        with c2:
            diastolic_bp       = st.number_input("Diastolic BP (mmHg)",     min_value=0, max_value=200, value=0)
            glucose_level      = st.number_input("Glucose Level (mg/dL)",   min_value=0.0, max_value=600.0, value=0.0, step=0.1)
            temperature_c      = st.number_input("Temperature (°C)",        min_value=0.0, max_value=43.0, value=0.0, step=0.1)
            height_cm          = st.number_input("Height (cm)",             min_value=0.0, max_value=250.0, value=0.0, step=0.5)
        symptoms = st.text_area("Symptoms (optional)", placeholder="e.g. mild headache, dizziness...")
        notes    = st.text_area("Additional Notes (optional)")
        submitted = st.form_submit_button("Submit Reading ✅", use_container_width=True)

        if submitted:
            def nz(v): return None if v == 0 else v

            warnings = []
            if systolic_bp > 0 and systolic_bp >= 140:
                warnings.append("⚠️ High systolic blood pressure (≥140 mmHg)")
            if diastolic_bp > 0 and diastolic_bp >= 90:
                warnings.append("⚠️ High diastolic blood pressure (≥90 mmHg)")
            if heart_rate > 0 and (heart_rate < 60 or heart_rate > 100):
                warnings.append(f"⚠️ Abnormal heart rate ({heart_rate} bpm)")
            if oxygen_saturation > 0 and oxygen_saturation < 95:
                warnings.append(f"⚠️ Low oxygen saturation ({oxygen_saturation}%)")
            if temperature_c > 0 and temperature_c > 37.5:
                warnings.append(f"⚠️ Elevated temperature ({temperature_c}°C)")
            if glucose_level > 0 and glucose_level > 140:
                warnings.append(f"⚠️ High glucose level ({glucose_level} mg/dL)")
            for w in warnings: st.warning(w)

            if height_cm > 0 and weight_kg > 0:
                bmi = weight_kg / ((height_cm/100)**2)
                cat = ("Underweight" if bmi<18.5 else "Normal weight" if bmi<25 else "Overweight" if bmi<30 else "Obese")
                st.info(f"📊 BMI: **{bmi:.1f}** ({cat})")

            try:
                result = monitoring_service.submit_vitals_and_assess(
                    patient_id=user["id"],
                    systolic_bp=nz(systolic_bp), diastolic_bp=nz(diastolic_bp),
                    heart_rate=nz(heart_rate), glucose_level=nz(glucose_level),
                    weight_kg=nz(weight_kg), temperature_c=nz(temperature_c),
                    oxygen_saturation=nz(oxygen_saturation),
                    symptoms=symptoms, notes=notes,
                )
                st.success(f"✅ Reading submitted at {result['vitals'].recorded_at}")

                severity = result.get("severity_report")
                if severity:
                    from app.ml.severity_engine import SEVERITY_COLORS
                    sev_level = severity.overall_severity
                    if sev_level == "critical":
                        st.error("🚨 **CRITICAL** — Your doctor has been alerted immediately!")
                    elif sev_level == "severe":
                        st.error("🔴 **SEVERE** — Your doctor has been notified urgently.")
                    elif sev_level == "moderate":
                        st.warning("🟠 **MODERATE** — Your doctor has been notified.")
                    elif sev_level == "mild":
                        st.warning("🟡 **MILD** — Please monitor your condition.")
                    else:
                        st.success("🟢 **NORMAL** — Your readings look stable.")
                    if severity.flags:
                        with st.expander(f"{severity.icon} View detailed assessment ({len(severity.flags)} findings)"):
                            for flag in severity.flags:
                                icon = SEVERITY_COLORS.get(flag.severity,"⚪")
                                st.write(f"{icon} **{flag.parameter}** ({flag.value}): {flag.message}")
                    if severity.should_alert_doctor:
                        st.info("📨 Your doctor has been sent an alert message automatically.")

                if result["predictions"]:
                    st.subheader("🤖 AI chronic disease risk")
                    cols = st.columns(len(result["predictions"]))
                    for col, pred in zip(cols, result["predictions"]):
                        icon = _RISK_COLORS.get(pred["risk_level"],"⚪")
                        col.metric(f"{icon} {pred['disease_type'].title()}", pred["risk_level"].upper(),
                                   f"{pred['risk_score']:.0%} probability")

            except ValidationError as e:
                st.error(str(e))

# ── History ───────────────────────────────────────────────────────
with history_tab:
    st.subheader("Your recent vitals history")
    history = vitals_service.get_history(user["id"], limit=30)
    if not history:
        st.info("No vitals submitted yet.")
    else:
        latest = history[0]
        st.markdown("#### Latest reading")
        m1,m2,m3,m4 = st.columns(4)
        m1.markdown(vital_card("Systolic BP", f"{latest.systolic_bp or '—'}", "mmHg", tone="info"), unsafe_allow_html=True)
        m2.markdown(vital_card("Heart Rate", f"{latest.heart_rate or '—'}", "bpm"), unsafe_allow_html=True)
        m3.markdown(vital_card("Glucose", f"{float(latest.glucose_level):.0f}" if latest.glucose_level else "—", "mg/dL", tone="amber"), unsafe_allow_html=True)
        m4.markdown(vital_card("SpO2", f"{latest.oxygen_saturation or '—'}", "%"), unsafe_allow_html=True)

        st.markdown("#### Trend charts")
        bp_records = [r for r in history if r.systolic_bp and r.diastolic_bp]
        if bp_records:
            st.plotly_chart(build_blood_pressure_chart(bp_records), use_container_width=True, key="history_bp")
        c1,c2 = st.columns(2)
        with c1:
            if any(r.heart_rate for r in history):
                st.plotly_chart(build_single_metric_chart(
                    history,"heart_rate","Heart Rate","bpm",normal_range=(60,100),color="#7E5AA2"),
                    use_container_width=True, key="history_hr")
        with c2:
            if any(r.glucose_level for r in history):
                st.plotly_chart(build_single_metric_chart(
                    history,"glucose_level","Glucose Level","mg/dL",normal_range=(70,140),color="#B8761D"),
                    use_container_width=True, key="history_glucose")
        st.markdown("#### Raw records table")
        st.dataframe([{
            "Date": r.recorded_at, "Systolic": r.systolic_bp, "Diastolic": r.diastolic_bp,
            "Heart Rate": r.heart_rate, "Glucose": r.glucose_level,
            "SpO2 (%)": r.oxygen_saturation, "Temp (°C)": r.temperature_c, "Symptoms": r.symptoms,
        } for r in history], use_container_width=True)

# ── AI Risk History ───────────────────────────────────────────────
with risk_tab:
    st.subheader("🤖 AI risk assessment history")
    try:
        diseases  = ["stroke","diabetes","hypertension"]
        found_any = False
        for disease in diseases:
            try:
                disease_preds = prediction_repo.get_history(user["id"], disease, limit=50)
                if not disease_preds: continue
                found_any = True
                import plotly.graph_objects as go
                timestamps = [p.predicted_at for p in disease_preds]
                scores     = [float(p.risk_score)*100 for p in disease_preds]
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=timestamps, y=scores, mode="lines+markers",
                    line=dict(color="#0E7A5C", width=2), marker=dict(size=7)))
                fig.add_hline(y=40, line_dash="dot", line_color="orange",  annotation_text="Medium risk (40%)")
                fig.add_hline(y=70, line_dash="dot", line_color="#C73E3A", annotation_text="High risk (70%)")
                fig.update_layout(title=f"{disease.title()} Risk Score Over Time",
                    xaxis_title="Date", yaxis_title="Risk (%)", yaxis=dict(range=[0,100]), margin=dict(t=60))
                st.plotly_chart(fig, use_container_width=True, key=f"risk_{disease}")
                latest_pred = disease_preds[-1]
                icon = _RISK_COLORS.get(latest_pred.risk_level,"⚪")
                st.write(f"**Latest {disease.title()} Risk:** {icon} {latest_pred.risk_level.upper()} "
                         f"({float(latest_pred.risk_score):.0%} probability)")
                st.divider()
            except Exception:
                pass
        if not found_any:
            st.info("No AI risk assessments yet. Submit vitals to get your first assessment.")
    except Exception as e:
        st.error(f"Could not load risk history: {e}")

# ── Download Report ───────────────────────────────────────────────
with report_tab:
    st.subheader("📄 Download your health report")
    c1, c2 = st.columns(2)
    with c1: report_format = st.selectbox("Format", ["PDF (.pdf)", "Text (.txt)", "CSV (.csv)"])
    if st.button("📥 Generate & Download Report", use_container_width=True):
        history = vitals_service.get_history(user["id"], limit=100)
        if not history:
            st.warning("No vitals data to include in report.")
        else:
            if report_format == "CSV (.csv)":
                import csv
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["Recorded At","Systolic BP","Diastolic BP","Heart Rate",
                                  "Glucose (mg/dL)","Weight (kg)","SpO2 (%)","Temperature (°C)","Symptoms"])
                for r in history:
                    writer.writerow([r.recorded_at,r.systolic_bp,r.diastolic_bp,r.heart_rate,
                                     r.glucose_level,r.weight_kg,r.oxygen_saturation,r.temperature_c,r.symptoms])
                st.download_button("⬇️ Download CSV Report", data=output.getvalue(),
                    file_name=f"health_report_{user['full_name'].replace(' ','_')}.csv", mime="text/csv")
            elif report_format == "PDF (.pdf)":
                from app.utils.pdf_generator import generate_health_report_pdf
                try:
                    patient = patient_repo.get_by_user_id(user["id"])
                    patient_info = {
                        "age": (datetime.now().date() - patient.date_of_birth).days // 365 if patient.date_of_birth else "N/A",
                        "gender": patient.gender or "N/A",
                        "conditions": list(patient.chronic_conditions) if patient.chronic_conditions else [],
                        "emergency_contact": patient.emergency_contact or "N/A",
                    }
                    # Get summary stats
                    bp_vals = [(r.systolic_bp, r.diastolic_bp) for r in history if r.systolic_bp and r.diastolic_bp]
                    hr_vals = [r.heart_rate for r in history if r.heart_rate]
                    glu_vals = [float(r.glucose_level) for r in history if r.glucose_level]
                    summary_stats = {
                        "avg_systolic": f"{sum(v[0] for v in bp_vals)/len(bp_vals):.0f}" if bp_vals else "N/A",
                        "avg_diastolic": f"{sum(v[1] for v in bp_vals)/len(bp_vals):.0f}" if bp_vals else "N/A",
                        "avg_hr": f"{sum(hr_vals)/len(hr_vals):.0f}" if hr_vals else "N/A",
                        "avg_glucose": f"{sum(glu_vals)/len(glu_vals):.0f}" if glu_vals else "N/A",
                    }
                    # Get predictions
                    from app.database.models import Prediction
                    all_preds = []
                    for disease in ["stroke", "diabetes", "hypertension"]:
                        preds = prediction_repo.get_history(user["id"], disease, limit=3)
                        for p in preds:
                            all_preds.append({
                                "disease_type": p.disease_type,
                                "risk_level": p.risk_level,
                                "risk_score": float(p.risk_score),
                                "model_version": p.model_version,
                            })
                    # Get medications
                    meds = medication_repo.list_for_patient(user["id"], active_only=False)
                    pdf_bytes = generate_health_report_pdf(
                        patient_name=user["full_name"],
                        patient_info=patient_info,
                        vitals_history=history,
                        predictions=all_preds if all_preds else None,
                        medications=meds if meds else None,
                        summary_stats=summary_stats,
                    )
                    st.download_button("⬇️ Download PDF Report", data=pdf_bytes,
                        file_name=f"health_report_{user['full_name'].replace(' ','_')}.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"Could not generate PDF: {e}")
            else:
                lines = ["="*60,"  REMOTE PATIENT MONITORING SYSTEM","  Personal Health Report","="*60,
                         f"Patient: {user['full_name']}",
                         f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
                         f"Total Readings: {len(history)}","","RECENT VITALS READINGS","-"*40]
                for r in history[:10]:
                    lines.append(f"\nDate: {r.recorded_at}")
                    if r.systolic_bp: lines.append(f"  Blood Pressure: {r.systolic_bp}/{r.diastolic_bp} mmHg")
                    if r.heart_rate:  lines.append(f"  Heart Rate: {r.heart_rate} bpm")
                    if r.glucose_level: lines.append(f"  Glucose: {float(r.glucose_level):.1f} mg/dL")
                    if r.oxygen_saturation: lines.append(f"  SpO2: {r.oxygen_saturation}%")
                    if r.temperature_c: lines.append(f"  Temperature: {float(r.temperature_c):.1f}°C")
                    if r.symptoms: lines.append(f"  Symptoms: {r.symptoms}")
                lines += ["","="*60,"DISCLAIMER: This is a decision-support tool only.","="*60]
                st.download_button("⬇️ Download Text Report", data="\n".join(lines),
                    file_name=f"health_report_{user['full_name'].replace(' ','_')}.txt", mime="text/plain")
            st.success("✅ Report ready!")

# ── Comprehensive Vitals Overview ────────────────────────────────
with vitals_chart_tab:
    st.subheader("📊 Comprehensive Vitals Overview")
    history_all = vitals_service.get_history(user["id"], limit=100)
    if not history_all:
        st.info("No vitals submitted yet. Submit a reading to see trend charts.")
    else:
        # Summary metrics
        latest = history_all[-1]
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.markdown(vital_card("Systolic BP", f"{latest.systolic_bp or '—'}", "mmHg", tone="info"), unsafe_allow_html=True)
        m2.markdown(vital_card("Diastolic BP", f"{latest.diastolic_bp or '—'}", "mmHg", tone="info"), unsafe_allow_html=True)
        m3.markdown(vital_card("Heart Rate", f"{latest.heart_rate or '—'}", "bpm"), unsafe_allow_html=True)
        m4.markdown(vital_card("Glucose", f"{float(latest.glucose_level):.0f}" if latest.glucose_level else "—", "mg/dL", tone="amber"), unsafe_allow_html=True)
        m5.markdown(vital_card("SpO2", f"{latest.oxygen_saturation or '—'}", "%"), unsafe_allow_html=True)
        m6.markdown(vital_card("Temp", f"{float(latest.temperature_c):.1f}" if latest.temperature_c else "—", "°C"), unsafe_allow_html=True)

        st.markdown("---")

        # Blood Pressure chart
        bp_records = [r for r in history_all if r.systolic_bp and r.diastolic_bp]
        if bp_records:
            st.plotly_chart(build_blood_pressure_chart(bp_records), use_container_width=True, key="overview_bp_chart")

        # Individual metric charts in 2x2 grid
        charts_data = [
            ("heart_rate", "Heart Rate", "bpm", (60, 100), "#7E5AA2"),
            ("glucose_level", "Glucose Level", "mg/dL", (70, 140), "#B8761D"),
            ("oxygen_saturation", "Oxygen Saturation (SpO2)", "%", (95, 100), "#0E7A5C"),
            ("temperature_c", "Body Temperature", "°C", (36.1, 37.5), "#C73E3A"),
            ("weight_kg", "Body Weight", "kg", None, "#2A6A9B"),
        ]

        for i in range(0, len(charts_data), 2):
            col1, col2 = st.columns(2)
            with col1:
                field, title, unit, norm_range, color = charts_data[i]
                if any(getattr(r, field) is not None for r in history_all):
                    st.plotly_chart(build_single_metric_chart(
                        history_all, field, title, unit,
                        normal_range=norm_range, color=color
                    ), use_container_width=True, key=f"overview_{field}_{i}")
                else:
                    st.info(f"No {title.lower()} data recorded yet.")
            with col2:
                if i + 1 < len(charts_data):
                    field, title, unit, norm_range, color = charts_data[i + 1]
                    if any(getattr(r, field) is not None for r in history_all):
                        st.plotly_chart(build_single_metric_chart(
                            history_all, field, title, unit,
                            normal_range=norm_range, color=color
                        ), use_container_width=True, key=f"overview_{field}_{i+1}")
                    else:
                        st.info(f"No {title.lower()} data recorded yet.")

        # Full vitals table
        with st.expander("📋 Full Vitals History Table", expanded=False):
                st.dataframe([{
                "Date": r.recorded_at,
                "Systolic": r.systolic_bp,
                "Diastolic": r.diastolic_bp,
                "Heart Rate": r.heart_rate,
                "Glucose": r.glucose_level,
                "SpO2 (%)": r.oxygen_saturation,
                "Temp (°C)": r.temperature_c,
                "Weight (kg)": r.weight_kg,
                "Symptoms": r.symptoms,
            } for r in reversed(history_all)], use_container_width=True)

        # Auto-refresh section
        st.markdown("---")
        auto_refresh = st.checkbox("🔄 Auto-refresh every 60 seconds", key="patient_auto_refresh")
        if auto_refresh:
            import time
            time.sleep(60)
            st.rerun()

# ── Health Score ─────────────────────────────────────────────────
with health_tab:
    st.subheader("🏥 Your Health Score")

    history_score = vitals_service.get_history(user["id"], limit=5)
    latest_vitals = history_score[-1] if history_score else None

    # Get BMI
    bmi = None
    if latest_vitals and latest_vitals.weight_kg:
        try:
            patient = patient_repo.get_by_user_id(user["id"])
            from app.utils.date_utils import calculate_age
            age = calculate_age(patient.date_of_birth)
            # Use latest weight with a default height estimate if not available
            bmi = float(latest_vitals.weight_kg) / (1.75 ** 2)  # rough estimate
        except Exception:
            pass

    # Get adherence
    adherence = medication_repo.get_adherence_rate(user["id"], days=30)

    # Get risk scores
    risk_scores = []
    for disease in ["stroke", "diabetes", "hypertension"]:
        preds = prediction_repo.get_history(user["id"], disease, limit=1)
        if preds:
            risk_scores.append(float(preds[-1].risk_score))

    result = health_score_svc.calculate(
        vitals=latest_vitals, bmi=bmi,
        adherence=adherence if adherence > 0 else None,
        latest_risk_scores=risk_scores if risk_scores else None,
    )

    # Score display
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        score = result["score"]
        color = result["color"]
        st.markdown(f"""
        <div style="text-align:center;background:white;border:2px solid {color};
             border-radius:16px;padding:32px 20px;">
            <div style="font-size:64px;font-weight:800;color:{color};
                 font-family:monospace;line-height:1;">{score}</div>
            <div style="font-size:16px;font-weight:600;color:{color};margin-top:4px;">
                {result['grade']}
            </div>
            <div style="font-size:11px;color:#5F717A;margin-top:4px;">
                out of 100
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("**Score Breakdown**")
        for key, val in result["breakdown"].items():
            label = {"bp": "Blood Pressure", "hr": "Heart Rate", "glucose": "Glucose",
                     "spo2": "SpO2", "temp": "Temperature", "bmi": "BMI",
                     "adherence": "Med Adherence", "risk": "AI Risk"}.get(key, key)
            bar_color = "#0E7A5C" if val >= 70 else "#B8761D" if val >= 40 else "#C73E3A"
            st.markdown(f"""
            <div style="margin-bottom:6px;">
                <div style="display:flex;justify-content:space-between;font-size:11px;">
                    <span>{label}</span><span style="font-weight:600;">{val}</span>
                </div>
                <div style="background:#DCE5E1;border-radius:4px;height:6px;">
                    <div style="background:{bar_color};width:{val}%;height:6px;border-radius:4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with c3:
        st.markdown("**Recommendations**")
        for rec in result["recommendations"]:
            st.info(rec)

# ── Health Timeline ──────────────────────────────────────────────
with timeline_tab:
    st.subheader("📅 Your Health Timeline")
    st.caption("A chronological view of all health events")

    timeline_events = []

    # Add vitals events
    for v in vitals_service.get_history(user["id"], limit=20):
        sev = "🟢"
        if v.systolic_bp and v.systolic_bp >= 140: sev = "🟠"
        if v.systolic_bp and v.systolic_bp >= 180: sev = "🔴"
        bp_str = f"{v.systolic_bp}/{v.diastolic_bp}" if v.systolic_bp and v.diastolic_bp else "—"
        timeline_events.append({
            "date": v.recorded_at,
            "type": "Vitals",
            "icon": sev,
            "title": f"Vitals Recorded: BP {bp_str}",
            "details": f"HR: {v.heart_rate or '—'} | Glucose: {v.glucose_level or '—'} | SpO2: {v.oxygen_saturation or '—'}",
        })

    # Add alert events
    for a in alert_repo.list_for_patient(user["id"], limit=10):
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(a.severity, "⚪")
        timeline_events.append({
            "date": a.created_at,
            "type": "Alert",
            "icon": icon,
            "title": f"AI Alert: {a.severity.upper()} Risk",
            "details": a.message[:100],
        })

    # Add appointment events
    for appt in appt_repo.get_for_patient(user["id"], upcoming_only=False)[:10]:
        status_icon = {"scheduled": "🔵", "completed": "✅", "cancelled": "❌"}.get(appt.status, "⚪")
        timeline_events.append({
            "date": appt.created_at or appt.appointment_date,
            "type": "Appointment",
            "icon": status_icon,
            "title": f"Appointment with Dr. {appt.doctor_name}",
            "details": f"{appt.appointment_date} | {appt.status.title()} | {appt.location}",
        })

    # Sort by date
    timeline_events.sort(key=lambda x: str(x["date"]), reverse=True)

    if not timeline_events:
        st.info("No health events recorded yet. Submit vitals to start your timeline.")
    else:
        for event in timeline_events[:30]:
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 4, 2])
                with c1:
                    st.markdown(f"### {event['icon']}")
                with c2:
                    st.markdown(f"**{event['title']}**")
                    st.caption(event["details"])
                with c3:
                    date_str = event["date"].strftime("%d %b %Y, %H:%M") if hasattr(event["date"], "strftime") else str(event["date"])[:16]
                    st.caption(f"📅 {date_str}")
                    st.caption(f"📂 {event['type']}")

if st.button("Log Out"):
    SessionManager.logout(); st.rerun()
