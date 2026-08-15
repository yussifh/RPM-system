"""
3_Doctor_Dashboard.py — THEMED VERSION
"""

import io, csv, streamlit as st
from datetime import datetime, date, timedelta, time as dt_time
from app.core.security import SessionManager
from app.core.exceptions import ValidationError
from app.services.doctor_service import DoctorService
from app.services.alert_service import AlertService
from app.services.emergency_contact_service import EmergencyContactService
from app.database.repositories.doctor_repository import DoctorRepository
from app.utils.prescription_generator import generate_prescription_pdf
from app.database.repositories.appointment_repository import AppointmentRepository
from app.database.repositories.doctor_schedule_repository import DoctorScheduleRepository
from app.utils.custom_css import apply_theme, profile_widget, stat_tiles, notification_bell, page_header, vital_card
from app.utils.visualizations import build_blood_pressure_chart, build_single_metric_chart

st.set_page_config(page_title="Doctor Dashboard", page_icon="🩻", layout="wide")
apply_theme()

user = SessionManager.require_role("doctor")
doctor_service = DoctorService()
alert_service  = AlertService()
emerg_service  = EmergencyContactService()
appt_repo      = AppointmentRepository()
doctor_schedule_repo = DoctorScheduleRepository()
doctor_repo = DoctorRepository()
doctor_info = doctor_repo.get_by_user_id(user["id"])

_RISK_ICONS = {"low":"🟢","medium":"🟡","high":"🟠","critical":"🔴"}
_SEV_ORDER  = {"critical":0,"high":1,"medium":2,"low":3}

def _to_time(val):
    if val is None:
        return None
    if isinstance(val, dt_time):
        return val
    if isinstance(val, timedelta):
        total = int(val.total_seconds())
        return dt_time(total // 3600, (total % 3600) // 60, total % 60)
    return val

open_alerts   = alert_service.list_open_for_doctor(user["id"])
alert_badge   = f" 🔴 {len(open_alerts)} alerts" if open_alerts else ""

# ── Sidebar ──────────────────────────────────────────────────────
profile_widget(user)
notification_bell(user)
patients_all = doctor_service.get_assigned_patients(user["id"])
stat_tiles([
    {"label": "Patients", "value": len(patients_all)},
    {"label": "Alerts",   "value": len(open_alerts)},
    {"label": "Resolved", "value": 0},
])

st.markdown(page_header("🩻", f"Doctor Dashboard{alert_badge}", f"Your patient overview — Dr. {user['full_name']}"), unsafe_allow_html=True)

alerts_tab, patients_tab, compare_tab, schedule_tab = st.tabs([
    f"🚨 Alerts ({len(open_alerts)})", "👥 My Patients", "📊 Comparison", "📅 Today's Schedule"
])

# ── Alerts ────────────────────────────────────────────────────────
with alerts_tab:
    st.subheader("Open alerts")
    if not open_alerts:
        st.success("✅ No open alerts. All patients are stable.")
    else:
        sorted_alerts = sorted(open_alerts, key=lambda a: _SEV_ORDER.get(a["severity"],99))
        for alert in sorted_alerts:
            icon = _RISK_ICONS.get(alert["severity"],"⚪")
            recs = {
                "critical": "🏥 **Immediate action required.** Contact patient now or escalate to emergency services.",
                "high":     "📞 **Call patient within 24 hours.** Review medication and schedule urgent appointment.",
                "medium":   "📋 **Monitor closely.** Schedule follow-up within 1 week.",
                "low":      "📝 **Note for next appointment.** No urgent action required.",
            }
            with st.container(border=True):
                c1, c2, c3 = st.columns([4,1,1])
                with c1:
                    st.markdown(f"{icon} **{alert['patient_name']}** — **{alert['severity'].upper()}** risk")
                    st.write(alert["message"])
                    st.caption(f"⏰ {alert['created_at']}")
                    rec = recs.get(alert["severity"],"")
                    if rec: st.info(rec)
                with c2:
                    if st.button("✅ Acknowledge", key=f"ack_{alert['id']}"):
                        alert_service.acknowledge(alert["id"], user["id"]); st.rerun()
                with c3:
                    if st.button("🔒 Resolve", key=f"res_{alert['id']}"):
                        alert_service.resolve(alert["id"]); st.rerun()

# ── My Patients ───────────────────────────────────────────────────
with patients_tab:
    patients = doctor_service.get_assigned_patients(user["id"])
    if not patients:
        st.info("No patients currently assigned to you.")
    else:
        patient_options = {(p.full_name or f"Patient #{p.user_id}"): p.user_id for p in patients}
        selected_name   = st.selectbox("Select a patient", list(patient_options.keys()))
        selected_id     = patient_options[selected_name]
        overview        = doctor_service.get_patient_overview(selected_id)
        patient         = overview["patient"]

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Age",        overview["age"])
        c2.metric("Gender",     patient.gender.title())
        c3.metric("Conditions", len(patient.chronic_conditions))
        c4.metric("Readings",   len(overview.get("vitals_history",[])))

        latest = overview.get("vitals_history", [None])[-1] if overview.get("vitals_history") else None
        if latest:
            st.markdown("#### Latest vitals")
            vc = st.columns(4)
            vc[0].markdown(vital_card("Systolic BP", f"{latest.systolic_bp or '—'}", "mmHg", tone="info"), unsafe_allow_html=True)
            vc[1].markdown(vital_card("Heart Rate", f"{latest.heart_rate or '—'}", "bpm"), unsafe_allow_html=True)
            vc[2].markdown(vital_card("Glucose", f"{float(latest.glucose_level):.0f}" if latest.glucose_level else "—", "mg/dL", tone="amber"), unsafe_allow_html=True)
            vc[3].markdown(vital_card("SpO2", f"{latest.oxygen_saturation or '—'}", "%"), unsafe_allow_html=True)

        if patient.chronic_conditions:
            st.write("**Chronic conditions:**", ", ".join(c.title() for c in patient.chronic_conditions))

        st.subheader("🤖 Latest AI risk assessment")
        if not overview["latest_predictions"]:
            st.caption("No AI predictions yet.")
        else:
            pc = st.columns(len(overview["latest_predictions"]))
            for col, pred in zip(pc, overview["latest_predictions"]):
                icon = _RISK_ICONS.get(pred.risk_level,"⚪")
                col.metric(f"{icon} {pred.disease_type.title()}", pred.risk_level.upper(),
                           f"{float(pred.risk_score):.0%} probability")

        st.subheader("📈 Vitals trends")
        history = overview.get("vitals_history",[])
        if not history:
            st.caption("No vitals submitted yet.")
        else:
            bp_records = [r for r in history if r.systolic_bp and r.diastolic_bp]
            if bp_records:
                st.plotly_chart(build_blood_pressure_chart(bp_records), width="stretch")
            c1,c2 = st.columns(2)
            with c1:
                if any(r.heart_rate for r in history):
                    st.plotly_chart(build_single_metric_chart(
                        history,"heart_rate","Heart Rate","bpm",normal_range=(60,100),color="#7E5AA2"),
                        width="stretch")
            with c2:
                if any(r.glucose_level for r in history):
                    st.plotly_chart(build_single_metric_chart(
                        history,"glucose_level","Glucose Level","mg/dL",normal_range=(70,140),color="#B8761D"),
                        width="stretch")

            st.subheader("📋 Vitals table")
            st.dataframe([{
                "Date": r.recorded_at, "Systolic": r.systolic_bp, "Diastolic": r.diastolic_bp,
                "Heart Rate": r.heart_rate, "Glucose": r.glucose_level,
                "SpO2 (%)": r.oxygen_saturation, "Symptoms": r.symptoms,
            } for r in history], width="stretch")

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Date","Systolic BP","Diastolic BP","Heart Rate","Glucose","SpO2","Temperature","Symptoms"])
            for r in history:
                writer.writerow([r.recorded_at,r.systolic_bp,r.diastolic_bp,r.heart_rate,
                                  r.glucose_level,r.oxygen_saturation,r.temperature_c,r.symptoms])
            st.download_button("📥 Export Patient Data (CSV)", data=output.getvalue(),
                file_name=f"patient_{selected_name.replace(' ','_')}_vitals.csv", mime="text/csv")

        st.subheader("📝 Clinical notes")
        with st.form(f"note_form_{selected_id}"):
            new_note = st.text_area("Add a clinical note")
            if st.form_submit_button("Add Note ✅"):
                try:
                    doctor_service.add_clinical_note(user["id"], selected_id, new_note)
                    st.success("Note added."); st.rerun()
                except ValidationError as e:
                    st.error(str(e))
        if overview.get("notes"):
            for note in overview["notes"]:
                with st.container(border=True):
                    st.write(note["note"])
                    st.caption(f"— Dr. {note['doctor_name']}, {note['created_at']}")
        else:
            st.caption("No clinical notes yet.")

        st.subheader("💊 Patient Medications")
        active_meds = doctor_service.get_patient_medications(selected_id, active_only=True)
        all_meds    = doctor_service.get_patient_medications(selected_id, active_only=False)
        past_meds   = [m for m in all_meds if not m.is_active]

        if active_meds:
            for med in active_meds:
                with st.container(border=True):
                    c1, c2 = st.columns([6, 1])
                    with c1:
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:12px;">
                            <div style="width:36px;height:36px;border-radius:50%;
                                 background:#0E7A5C;color:white;display:flex;
                                 align-items:center;justify-content:center;
                                 font-size:16px;">💊</div>
                            <div>
                                <strong style="font-size:14px;">{med.name}</strong>
                                <br>
                                <span style="color:#5F717A;font-size:12px;">
                                    {med.dosage} — {med.frequency} — {med.route}
                                </span>
                                <br>
                                <span style="color:#5F717A;font-size:11px;">
                                    Started: {med.start_date}
                                    {f" | Prescribed by: {med.prescribed_by}" if med.prescribed_by else ""}
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if med.notes:
                            st.caption(f"📝 {med.notes}")
                    with c2:
                        st.markdown(f"""
                        <div style="background:#E7F4EF;border:1px solid #E7F4EF;
                             border-radius:8px;padding:8px 12px;text-align:center;">
                            <span style="font-size:11px;font-weight:600;
                                  color:#0E7A5C;text-transform:uppercase;">Active</span>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("No active medications recorded for this patient.")

        if past_meds:
            with st.expander(f"🗂️ Past Medications ({len(past_meds)})"):
                for med in past_meds:
                    st.markdown(f"~~{med.name}~~ — {med.dosage} "
                                f"({med.frequency}) | Stopped: {med.end_date or 'Unknown'}")

        adherence = doctor_service.get_patient_medication_adherence(selected_id, days=30)
        if active_meds:
            a_color = "#0E7A5C" if adherence >= 80 else "#B8761D" if adherence >= 50 else "#C73E3A"
            st.markdown(f"""
            <div style="background:white;border:1px solid #DCE5E1;border-radius:10px;
                 padding:14px;display:flex;align-items:center;justify-content:space-between;
                 margin-top:8px;">
                <div>
                    <div style="font-size:11px;font-weight:600;text-transform:uppercase;
                         color:#5F717A;letter-spacing:.03em;">30-Day Medication Adherence</div>
                    <div style="font-size:11px;color:#5F717A;margin-top:2px;">
                        Based on the patient's daily medication logs
                    </div>
                </div>
                <div style="font-size:28px;font-weight:800;color:{a_color};font-family:monospace;">
                    {adherence}%
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Drug interaction check
            from app.services.medication_interaction_service import MedicationInteractionService
            interaction_svc = MedicationInteractionService()
            active_med_names = [m.name for m in active_meds]
            interactions = interaction_svc.check_interactions(active_med_names)
            if interactions:
                st.divider()
                st.subheader("⚠️ Drug Interaction Warnings")
                for interaction in interactions:
                    severity_color = "#C73E3A" if interaction["severity"] == "severe" else "#B8761D"
                    st.markdown(f"""
                    <div style="background:#FBF3E4;border:1px solid {severity_color};border-radius:8px;
                         padding:12px 16px;margin-bottom:8px;">
                        <div style="font-weight:600;color:{severity_color};">
                            {interaction['severity'].upper()} Interaction
                        </div>
                        <div style="font-size:13px;margin-top:4px;">
                            <strong>{interaction['drug_a']}</strong> + <strong>{interaction['drug_b']}</strong>
                        </div>
                        <div style="font-size:12px;color:#5F717A;margin-top:4px;">
                            {interaction['description']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        st.subheader("🚨 Emergency Contact Notifications")
        emerg_notifs = emerg_service.get_patient_notifications(selected_id)
        if emerg_notifs:
            for notif in emerg_notifs:
                sev_color = "#C73E3A" if notif.severity == "critical" else "#B8761D"
                status_icon = "✅" if notif.status == "acknowledged" else "⏳"
                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:10px;">
                            <div style="width:32px;height:32px;border-radius:50%;
                                 background:{sev_color};color:white;display:flex;
                                 align-items:center;justify-content:center;
                                 font-size:14px;">🚨</div>
                            <div>
                                <strong style="font-size:13px;color:{sev_color};">
                                    {notif.severity.upper()} — Emergency Contact Notified
                                </strong>
                                <br>
                                <span style="color:#5F717A;font-size:12px;">
                                    Contact: {notif.emergency_contact}
                                </span>
                                <br>
                                <span style="color:#5F717A;font-size:11px;">
                                    {notif.created_at}
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if notif.vital_snapshot:
                            st.caption(f"📊 Vitals: {notif.vital_snapshot}")
                    with c2:
                        st.markdown(f"{status_icon} {notif.status.title()}")
        else:
            st.info("No emergency contact notifications for this patient.")

        # Prescription PDF generation
        st.markdown("---")
        st.subheader("🖨️ Print Prescription")
        with st.expander("Generate printable prescription"):
            # Get active medications
            meds = doctor_service.get_patient_medications(selected_id)
            active_meds = [m for m in meds if m.is_active]

            if not active_meds:
                st.info("No active medications to include in prescription.")
            else:
                with st.form("prescription_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        diagnosis = st.text_input("Diagnosis", placeholder="e.g., Hypertension Stage 2")
                        instructions = st.text_area("Additional Instructions",
                            placeholder="e.g., Take medication with food, avoid salt...")
                    with c2:
                        doctor_notes = st.text_area("Doctor's Notes",
                            placeholder="e.g., Follow up in 2 weeks, monitor BP daily...")
                        signature_name = st.text_input("Signature Name", value=user["full_name"] or "")

                    submitted = st.form_submit_button("📄 Generate Prescription PDF", width="stretch")
                    if submitted:
                        if not diagnosis:
                            st.error("Please enter a diagnosis.")
                        else:
                            try:
                                patient = overview["patient"]
                                pdf_bytes = generate_prescription_pdf(
                                    doctor_name=signature_name or user["full_name"],
                                    doctor_specialization=doctor_info.specialization or "General Practice",
                                    patient_name=patient.full_name or "Unknown",
                                    patient_age=overview["age"],
                                    patient_gender=patient.gender or "—",
                                    medications=[{
                                        "name": m.name,
                                        "dosage": m.dosage,
                                        "frequency": m.frequency,
                                        "duration": f"{m.start_date} → {m.end_date}" if m.end_date else f"from {m.start_date}",
                                        "instructions": m.notes,
                                    } for m in active_meds],
                                    diagnosis=diagnosis,
                                    notes=instructions or doctor_notes or "No additional instructions.",
                                )
                                st.download_button(
                                    "⬇️ Download Prescription PDF",
                                    data=pdf_bytes,
                                    file_name=f"prescription_{str(patient.full_name or 'patient').replace(' ','_')}.pdf",
                                    mime="application/pdf",
                                    width="stretch",
                                )
                                st.success("✅ Prescription PDF generated!")
                            except Exception as e:
                                st.error(f"Error generating PDF: {e}")

# ── Patient Comparison ────────────────────────────────────────────
with compare_tab:
    st.subheader("📊 Patient risk comparison")
    if not patients:
        st.info("No patients assigned.")
    else:
        import plotly.graph_objects as go, pandas as pd
        comparison_data = []
        for p in patients:
            try:
                ov = doctor_service.get_patient_overview(p.user_id)
                for pred in ov.get("latest_predictions",[]):
                    comparison_data.append({
                        "Patient": p.full_name or f"Patient #{p.user_id}",
                        "Disease": pred.disease_type.title(),
                        "Risk Score (%)": float(pred.risk_score)*100,
                        "Risk Level": pred.risk_level,
                    })
            except Exception:
                pass
        if not comparison_data:
            st.info("No AI predictions available yet.")
        else:
            df = pd.DataFrame(comparison_data)
            colors = {"low":"#0E7A5C","medium":"#D99A1F","high":"#B8761D","critical":"#C73E3A"}
            fig = go.Figure()
            for disease in df["Disease"].unique():
                d = df[df["Disease"]==disease]
                fig.add_trace(go.Bar(
                    name=disease, x=d["Patient"], y=d["Risk Score (%)"],
                    marker_color=[colors.get(l,"#888") for l in d["Risk Level"]],
                ))
            fig.update_layout(barmode="group", title="Patient Risk Score Comparison",
                              xaxis_title="Patient", yaxis_title="Risk (%)",
                              yaxis=dict(range=[0,100]))
            st.plotly_chart(fig, width="stretch")
            st.dataframe(df, width="stretch")
            crit = df[df["Risk Level"]=="critical"]
            if not crit.empty:
                st.error(f"🔴 **{len(crit)} critical risk reading(s) require immediate attention!**")

# ── Today's Schedule ──────────────────────────────────────────────
with schedule_tab:
    st.subheader("📅 Today's Appointment Schedule")
    today = date.today()
    today_str = today.strftime("%A, %d %B %Y")
    st.caption(f"Viewing schedule for {today_str}")

    all_appts = appt_repo.get_for_doctor(user["id"], upcoming_only=False)
    today_appts = [a for a in all_appts if a.appointment_date == today]
    upcoming_appts = [a for a in all_appts if a.appointment_date > today and a.status == "scheduled"]

    _STATUS_ICONS = {
        "scheduled": "🔵", "completed": "✅", "cancelled": "❌", "pending": "⏳"
    }
    _SEVERITY_COLORS = {
        "critical": "#C73E3A", "high": "#B8761D", "moderate": "#2A6A9B", "low": "#0E7A5C"
    }

    if not today_appts:
        st.info("No appointments scheduled for today.")
    else:
        st.markdown(f"**{len(today_appts)} appointment(s) today**")
        for appt in today_appts:
            sev_color = _SEVERITY_COLORS.get(appt.severity_level, "#5F717A")
            status_icon = _STATUS_ICONS.get(appt.status, "🔵")
            time_str = appt.appointment_time.strftime("%I:%M %p") if hasattr(appt.appointment_time, "strftime") else str(appt.appointment_time)
            with st.container(border=True):
                c1, c2, c3 = st.columns([4, 2, 1])
                with c1:
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;">
                        <div style="width:40px;height:40px;border-radius:50%;
                             background:{sev_color};color:white;display:flex;
                             align-items:center;justify-content:center;
                             font-size:16px;font-weight:800;">
                            {time_str[:5]}
                        </div>
                        <div>
                            <strong style="font-size:14px;">{appt.patient_name}</strong>
                            <br>
                            <span style="color:#5F717A;font-size:12px;">
                                {appt.location} | {appt.severity_level.title()}
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if appt.reason:
                        st.caption(f"📋 {appt.reason}")
                with c2:
                    st.markdown(f"{status_icon} {appt.status.title()}")
                with c3:
                    if appt.status == "scheduled":
                        if st.button("✅ Complete", key=f"comp_{appt.id}"):
                            appt_repo.update_status(appt.id, "completed")
                            st.rerun()

    if upcoming_appts:
        st.markdown("---")
        st.subheader("📆 Upcoming Appointments")
        st.caption(f"{len(upcoming_appts)} upcoming appointment(s)")
        for appt in upcoming_appts[:5]:
            sev_color = _SEVERITY_COLORS.get(appt.severity_level, "#5F717A")
            time_str = appt.appointment_time.strftime("%I:%M %p") if hasattr(appt.appointment_time, "strftime") else str(appt.appointment_time)
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;">
                        <div style="width:8px;height:36px;border-radius:4px;background:{sev_color};"></div>
                        <div>
                            <strong style="font-size:13px;">{appt.patient_name}</strong>
                            <br>
                            <span style="color:#5F717A;font-size:12px;">
                                {appt.appointment_date} at {time_str} | {appt.location}
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    st.markdown(f"🔵 Scheduled")

    # Doctor availability schedule management
    st.divider()
    st.subheader("🗓️ My Availability Schedule")
    st.caption("Set your available hours for each day of the week")

    days_of_week = [0, 1, 2, 3, 4, 5, 6]
    day_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for i, (day, label) in enumerate(zip(days_of_week, day_labels)):
        schedules = doctor_schedule_repo.get_schedule_for_day(user["id"], day)
        schedule = schedules[0] if schedules else None
        with st.expander(f"📅 {label}", expanded=(day in [0, 1, 2, 3, 4])):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                is_available = st.checkbox(
                    "Available", value=schedule.is_active if schedule else False,
                    key=f"avail_{day}"
                )
            with c2:
                start_time = st.time_input(
                    "Start Time",
                    value=_to_time(schedule.start_time) if schedule and schedule.start_time else datetime.strptime("09:00", "%H:%M").time(),
                    key=f"start_{day}"
                )
                end_time = st.time_input(
                    "End Time",
                    value=_to_time(schedule.end_time) if schedule and schedule.end_time else datetime.strptime("17:00", "%H:%M").time(),
                    key=f"end_{day}"
                )
            with c3:
                if is_available and st.button("💾 Save", key=f"save_{day}"):
                    doctor_schedule_repo.set_schedule(
                        doctor_id=user["id"],
                        day_of_week=day,
                        start_time=start_time,
                        end_time=end_time,
                    )
                    st.success(f"✅ {label} schedule updated!")
                    st.rerun()
                if not is_available and schedule and st.button("🗑️ Clear", key=f"clear_{day}"):
                    doctor_schedule_repo.delete_schedule(schedule.id)
                    st.success(f"✅ {label} cleared!")
                    st.rerun()

    # Auto-refresh section
    st.markdown("---")
    auto_refresh = st.checkbox("🔄 Auto-refresh every 60 seconds", key="doctor_auto_refresh")
    if auto_refresh:
        import time
        time.sleep(60)
        st.rerun()

if st.button("Log Out"):
    SessionManager.logout(); st.rerun()
