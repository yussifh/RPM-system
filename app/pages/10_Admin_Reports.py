"""
10_Admin_Reports.py
--------------------
Admin Reports & Data Export page — system analytics, patient reports,
clinical reports, and operational data management with CSV exports.
"""

import io, csv
import streamlit as st
import plotly.graph_objects as go
from datetime import date, datetime, timedelta

from app.core.security import SessionManager
from app.services.admin_service import AdminService
from app.database.repositories.vitals_repository import VitalsRepository
from app.database.repositories.prediction_repository import PredictionRepository
from app.database.repositories.medication_repository import MedicationRepository
from app.database.repositories.alert_repository import AlertRepository
from app.database.repositories.patient_repository import PatientRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.clinical_note_repository import ClinicalNoteRepository
from app.database.repositories.appointment_repository import AppointmentRepository
from app.database.repositories.audit_log_repository import AuditLogRepository
from app.utils.custom_css import apply_theme, profile_widget, stat_tiles, notification_bell, page_header

st.set_page_config(page_title="Admin Reports", page_icon=":material/analytics:", layout="wide")
apply_theme()

user = SessionManager.require_role("admin")

admin_service    = AdminService()
vitals_repo      = VitalsRepository()
prediction_repo  = PredictionRepository()
med_repo         = MedicationRepository()
alert_repo       = AlertRepository()
patient_repo     = PatientRepository()
user_repo        = UserRepository()
note_repo        = ClinicalNoteRepository()
appt_repo        = AppointmentRepository()
audit_repo       = AuditLogRepository()

profile_widget(user)
notification_bell(user)

stats = admin_service.get_system_stats()
stat_tiles([
    {"label": "Patients", "value": stats["patient_count"]},
    {"label": "Doctors",  "value": stats["doctor_count"]},
    {"label": "Alerts",   "value": sum(stats.get("open_alerts_by_severity", {}).values())},
])

st.markdown(page_header(":material/analytics:", "Admin Reports & Data Export", "System analytics, clinical data, and operational reports"), unsafe_allow_html=True)

analytics_tab, patients_tab, clinical_tab, operations_tab, export_tab = st.tabs([
    ":material/bar_chart: System Analytics", ":material/group: Patient Reports", ":material/local_hospital: Clinical reports",
    ":material/settings: Operations", ":material/inbox: Bulk export"
])


def _to_csv(data: list[dict]) -> str:
    if not data:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()


# ================================================================
# TAB 1: System Analytics
# ================================================================
with analytics_tab:
    st.subheader("System Analytics Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(":material/group: Patients", stats["patient_count"])
    c2.metric(":material/stethoscope: Doctors", stats["doctor_count"])
    c3.metric(":material/construction: Admins", stats["admin_count"])
    c4.metric(":material/person: Total Users", stats["patient_count"] + stats["doctor_count"] + stats["admin_count"])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### User Distribution")
        fig = go.Figure(data=[go.Pie(
            labels=["Patients", "Doctors", "Admins"],
            values=[stats["patient_count"], stats["doctor_count"], stats["admin_count"]],
            hole=0.45,
            marker_colors=["#12A085", "#2A6A9B", "#B8761D"],
        )])
        fig.update_layout(margin=dict(t=10, b=10), height=280,
                          legend=dict(font=dict(size=11)))
        st.plotly_chart(fig, width="stretch")

    with c2:
        st.markdown("#### Open Alerts by Severity")
        severity_counts = stats.get("open_alerts_by_severity", {})
        if not severity_counts:
            st.success("No open alerts system-wide.")
        else:
            severities = ["critical", "high", "medium", "low"]
            counts = [severity_counts.get(s, 0) for s in severities]
            colors = ["#C73E3A", "#B8761D", "#2A6A9B", "#0E7A5C"]
            fig2 = go.Figure(data=[go.Bar(
                x=[s.title() for s in severities], y=counts,
                marker_color=colors, text=counts, textposition="auto",
            )])
            fig2.update_layout(margin=dict(t=10, b=10), height=280, showlegend=False)
            st.plotly_chart(fig2, width="stretch")

    st.markdown("#### Vitals Collection Summary")
    vitals_stats = vitals_repo.get_summary_stats()
    if vitals_stats and vitals_stats.get("total_readings"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Readings", vitals_stats["total_readings"])
        c2.metric("Patients with Data", vitals_stats["patients_with_readings"])
        c3.metric("Avg Systolic BP", f"{vitals_stats['avg_systolic']} mmHg")
        c4.metric("Avg Glucose", f"{vitals_stats['avg_glucose']} mg/dL")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg Heart Rate", f"{vitals_stats['avg_heart_rate']} bpm")
        c2.metric("Avg Diastolic BP", f"{vitals_stats['avg_diastolic']} mmHg")
        earliest = vitals_stats.get("earliest_reading")
        latest = vitals_stats.get("latest_reading")
        c3.metric("First Reading", earliest.strftime("%d %b %Y") if earliest else "—")
        c4.metric("Latest Reading", latest.strftime("%d %b %Y") if latest else "—")
    else:
        st.info("No vitals data collected yet.")

    st.markdown("#### Alert Statistics")
    alert_stats = alert_repo.get_alert_stats()
    if alert_stats and alert_stats.get("total_alerts"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Alerts", alert_stats["total_alerts"])
        c2.metric("Open", alert_stats.get("open_count", 0))
        c3.metric("Acknowledged", alert_stats.get("acknowledged_count", 0))
        c4.metric("Resolved", alert_stats.get("resolved_count", 0))
    else:
        st.info("No alerts generated yet.")


# ================================================================
# TAB 2: Patient Reports
# ================================================================
with patients_tab:
    st.subheader("Patient Reports")

    patients = patient_repo.list_all()
    doctors = admin_service.doctor_repo.list_all()

    st.markdown("#### Patient Directory")
    if patients:
        patient_data = []
        for p in patients:
            doctor_name = "—"
            if p.assigned_doctor_id:
                try:
                    doc_user = user_repo.get_by_id(p.assigned_doctor_id)
                    doctor_name = doc_user.full_name
                except Exception:
                    doctor_name = f"Doctor #{p.assigned_doctor_id}"
            patient_data.append({
                "ID": p.user_id,
                "Name": p.full_name or f"Patient #{p.user_id}",
                "Email": p.email or "—",
                "Gender": p.gender.title() if p.gender else "—",
                "DOB": p.date_of_birth,
                "Conditions": ", ".join(c.title() for c in p.chronic_conditions) if p.chronic_conditions else "—",
                "Assigned Doctor": doctor_name,
                "Status": "Active" if p.is_active else "Inactive",
            })

        st.dataframe(patient_data, width="stretch")

        csv_data = _to_csv(patient_data)
        st.download_button(
            ":material/inbox: Export Patient Directory (CSV)", data=csv_data,
            file_name=f"patient_directory_{date.today()}.csv", mime="text/csv",
            use_container_width=False,
        )
    else:
        st.info("No patients registered yet.")

    st.markdown("#### Patient Vitals Overview")
    vitals_data = vitals_repo.get_all_with_patients(limit=200)
    if vitals_data:
        st.write(f"**{len(vitals_data)} vitals records found**")
        display_data = [{
            "Patient": v["patient_name"],
            "Date": v["recorded_at"],
            "Systolic": v["systolic_bp"],
            "Diastolic": v["diastolic_bp"],
            "Heart Rate": v["heart_rate"],
            "Glucose": v["glucose_level"],
            "SpO2": v["oxygen_saturation"],
            "Symptoms": v["symptoms"],
        } for v in vitals_data]
        st.dataframe(display_data, width="stretch")

        csv_data = _to_csv(display_data)
        st.download_button(
            ":material/inbox: Export All Vitals (CSV)", data=csv_data,
            file_name=f"all_vitals_{date.today()}.csv", mime="text/csv",
        )
    else:
        st.info("No vitals records yet.")


# ================================================================
# TAB 3: Clinical Reports
# ================================================================
with clinical_tab:
    st.subheader("Clinical Reports")

    risk_tab_inner, meds_tab, alerts_tab_inner, notes_tab = st.tabs([
        ":material/smart_toy: AI Risk Assessments", ":material/medication: Medications", ":material/warning: Alerts", ":material/edit_note: Clinical notes"
    ])

    with risk_tab_inner:
        st.markdown("#### AI Risk Assessments — All Patients")
        predictions = prediction_repo.get_all_with_patients(limit=200)
        if predictions:
            pred_data = [{
                "Patient": p["patient_name"],
                "Disease": p["disease_type"].title(),
                "Risk Score": f'{float(p["risk_score"]):.1%}',
                "Risk Level": p["risk_level"].title(),
                "Model": p["model_version"],
                "Date": p["predicted_at"],
            } for p in predictions]
            st.dataframe(pred_data, width="stretch")

            st.markdown("#### Risk Distribution")
            risk_dist = prediction_repo.get_risk_distribution()
            if risk_dist:
                fig = go.Figure()
                diseases = list(set(r["disease_type"] for r in risk_dist))
                risk_levels = ["low", "medium", "high", "critical"]
                risk_colors = {"low": "#0E7A5C", "medium": "#D99A1F", "high": "#B8761D", "critical": "#C73E3A"}
                for disease in diseases:
                    disease_data = [r for r in risk_dist if r["disease_type"] == disease]
                    levels = [r["risk_level"] for r in disease_data]
                    counts = [r["patient_count"] for r in disease_data]
                    fig.add_trace(go.Bar(
                        name=disease.title(), x=levels, y=counts,
                        marker_color=[risk_colors.get(l, "#888") for l in levels],
                    ))
                fig.update_layout(barmode="group", title="Risk Level Distribution by Disease",
                                  xaxis_title="Risk Level", yaxis_title="Patient Count",
                                  height=300, margin=dict(t=50))
                st.plotly_chart(fig, width="stretch")

            csv_data = _to_csv(pred_data)
            st.download_button(            ":material/inbox: Export Risk Assessments (CSV)", data=csv_data,
                               file_name=f"risk_assessments_{date.today()}.csv", mime="text/csv")
        else:
            st.info("No AI risk assessments yet.")

    with meds_tab:
        st.markdown("#### Medication Summary — All Patients")
        all_meds = med_repo.get_all_with_patients(active_only=False, limit=200)
        if all_meds:
            med_data = [{
                "Patient": m.patient_name or f"Patient #{m.patient_id}",
                "Medication": m.name,
                "Dosage": m.dosage,
                "Frequency": m.frequency,
                "Route": m.route,
                "Prescribed By": m.prescribed_by or "—",
                "Start Date": m.start_date,
                "End Date": m.end_date or "—",
                "Status": "Active" if m.is_active else "Stopped",
            } for m in all_meds]
            st.dataframe(med_data, width="stretch")

            csv_data = _to_csv(med_data)
            st.download_button(            ":material/inbox: Export Medications (CSV)", data=csv_data,
                               file_name=f"medications_{date.today()}.csv", mime="text/csv")
        else:
            st.info("No medications recorded.")

        st.markdown("#### Medication Adherence (30-Day)")
        adherence = med_repo.get_adherence_summary()
        if adherence:
            st.dataframe([{
                "Patient": a["patient_name"],
                "Total Doses": a["total_logs"],
                "Taken": a["taken_count"],
                "Adherence Rate": f"{a['adherence_rate']}%",
            } for a in adherence], width="stretch")
        else:
            st.info("No medication logs yet.")

    with alerts_tab_inner:
        st.markdown("#### All Alerts")
        all_alerts = alert_repo.get_all_with_patients(limit=200)
        if all_alerts:
            alert_data = [{
                "ID": a["id"],
                "Patient": a["patient_name"],
                "Severity": a["severity"].title(),
                "Message": a["message"],
                "Status": a["status"].title(),
                "Acknowledged By": a.get("acknowledged_by_name") or "—",
                "Created": a["created_at"],
                "Resolved": a["resolved_at"] or "—",
            } for a in all_alerts]
            st.dataframe(alert_data, width="stretch")

            csv_data = _to_csv(alert_data)
            st.download_button(            ":material/inbox: Export Alerts (CSV)", data=csv_data,
                               file_name=f"alerts_{date.today()}.csv", mime="text/csv")
        else:
            st.info("No alerts generated yet.")

    with notes_tab:
        st.markdown("#### Clinical Notes — All Patients")
        patients = patient_repo.list_all()
        all_notes = []
        for p in patients:
            notes = note_repo.list_for_patient(p.user_id)
            for n in notes:
                all_notes.append({
                    "Patient": p.full_name or f"Patient #{p.user_id}",
                    "Doctor": n.get("doctor_name", "—"),
                    "Note": n["note"],
                    "Date": n["created_at"],
                })
        if all_notes:
            st.dataframe(all_notes, width="stretch")
            csv_data = _to_csv(all_notes)
            st.download_button(            ":material/inbox: Export Clinical Notes (CSV)", data=csv_data,
                               file_name=f"clinical_notes_{date.today()}.csv", mime="text/csv")
        else:
            st.info("No clinical notes yet.")


# ================================================================
# TAB 4: Operations
# ================================================================
with operations_tab:
    st.subheader("Operational Reports")

    st.markdown("#### Appointments Overview")
    patients = patient_repo.list_all()
    all_appts = []
    for p in patients:
        appts = appt_repo.get_for_patient(p.user_id)
        for a in appts:
            all_appts.append({
                "Patient": p.full_name or f"Patient #{p.user_id}",
                "Doctor": a.doctor_name or "—",
                "Date": a.appointment_date,
                "Time": a.appointment_time,
                "Location": a.location,
                "Reason": a.reason or "—",
                "Severity": a.severity_level or "—",
                "Status": a.status.title(),
            })
    if all_appts:
        st.dataframe(all_appts, width="stretch")
        csv_data = _to_csv(all_appts)
        st.download_button(        ":material/inbox: Export Appointments (CSV)", data=csv_data,
                           file_name=f"appointments_{date.today()}.csv", mime="text/csv")
    else:
        st.info("No appointments scheduled yet.")

    st.markdown("#### Audit Log")
    audit_logs = admin_service.get_recent_audit_logs(limit=200)
    if audit_logs:
        audit_data = [{
            "Time": log["created_at"],
            "User": log.get("user_name") or "System",
            "Action": log["action"],
            "Details": log["details"],
        } for log in audit_logs]
        st.dataframe(audit_data, width="stretch")

        csv_data = _to_csv(audit_data)
        st.download_button(        ":material/inbox: Export Audit Log (CSV)", data=csv_data,
                           file_name=f"audit_log_{date.today()}.csv", mime="text/csv")
    else:
        st.info("No audit log entries yet.")


# ================================================================
# TAB 5: Bulk Export
# ================================================================
with export_tab:
    st.subheader("Bulk Data Export")
    st.info("Select datasets to export. All exports are in CSV format.")

    export_options = st.multiselect(
        "Select datasets to export",
        ["Patient Directory", "All Vitals", "AI Risk Assessments",
         "Medications", "Alerts", "Clinical Notes", "Appointments", "Audit Log"],
        default=["Patient Directory", "All Vitals"],
    )

    if st.button(":material/inbox: Generate Export Package", width="stretch"):
        files = {}

        if "Patient Directory" in export_options:
            patients = patient_repo.list_all()
            data = [{
                "ID": p.user_id, "Name": p.full_name, "Email": p.email,
                "Gender": p.gender, "DOB": p.date_of_birth,
                "Conditions": ",".join(p.chronic_conditions) if p.chronic_conditions else "",
                "Doctor ID": p.assigned_doctor_id or "",
                "Active": p.is_active,
            } for p in patients]
            files["patient_directory.csv"] = _to_csv(data)

        if "All Vitals" in export_options:
            vitals = vitals_repo.get_all_with_patients(limit=2000)
            data = [{
                "Patient": v["patient_name"], "Date": v["recorded_at"],
                "Systolic": v["systolic_bp"], "Diastolic": v["diastolic_bp"],
                "Heart Rate": v["heart_rate"], "Glucose": v["glucose_level"],
                "Weight": v["weight_kg"], "SpO2": v["oxygen_saturation"],
                "Temperature": v["temperature_c"], "Symptoms": v["symptoms"],
            } for v in vitals]
            files["vitals_data.csv"] = _to_csv(data)

        if "AI Risk Assessments" in export_options:
            preds = prediction_repo.get_all_with_patients(limit=2000)
            data = [{
                "Patient": p["patient_name"], "Disease": p["disease_type"],
                "Risk Score": float(p["risk_score"]), "Risk Level": p["risk_level"],
                "Model": p["model_version"], "Date": p["predicted_at"],
            } for p in preds]
            files["risk_assessments.csv"] = _to_csv(data)

        if "Medications" in export_options:
            meds = med_repo.get_all_with_patients(active_only=False, limit=2000)
            data = [{
                "Patient": m.patient_name or f"Patient #{m.patient_id}", "Medication": m.name,
                "Dosage": m.dosage, "Frequency": m.frequency,
                "Route": m.route, "Prescribed By": m.prescribed_by or "",
                "Start": m.start_date, "End": m.end_date or "",
                "Active": m.is_active,
            } for m in meds]
            files["medications.csv"] = _to_csv(data)

        if "Alerts" in export_options:
            alerts = alert_repo.get_all_with_patients(limit=2000)
            data = [{
                "ID": a["id"], "Patient": a["patient_name"],
                "Severity": a["severity"], "Status": a["status"],
                "Message": a["message"], "Created": a["created_at"],
            } for a in alerts]
            files["alerts.csv"] = _to_csv(data)

        if "Clinical Notes" in export_options:
            patients = patient_repo.list_all()
            data = []
            for p in patients:
                notes = note_repo.list_for_patient(p.user_id)
                for n in notes:
                    data.append({
                        "Patient": p.full_name, "Doctor": n.get("doctor_name", ""),
                        "Note": n["note"], "Date": n["created_at"],
                    })
            files["clinical_notes.csv"] = _to_csv(data)

        if "Appointments" in export_options:
            patients = patient_repo.list_all()
            data = []
            for p in patients:
                appts = appt_repo.get_for_patient(p.user_id)
                for a in appts:
                    data.append({
                        "Patient": p.full_name, "Doctor": a.doctor_name or "",
                        "Date": a.appointment_date, "Time": a.appointment_time,
                        "Location": a.location, "Status": a.status,
                    })
            files["appointments.csv"] = _to_csv(data)

        if "Audit Log" in export_options:
            logs = audit_repo.list_recent(limit=2000)
            data = [{
                "Time": l["created_at"], "User": l.get("user_name", "System"),
                "Action": l["action"], "Details": l["details"],
            } for l in logs]
            files["audit_log.csv"] = _to_csv(data)

        if files:
            combined = "\n".join(f"--- {name} ---\n{content}" for name, content in files.items())
            st.success(f":material/check_circle: Generated {len(files)} export file(s)")
            for name, content in files.items():
                st.download_button(
                    f":material/inbox: {name}", data=content,
                    file_name=f"{date.today()}_{name}", mime="text/csv",
                )
        else:
            st.warning("No data to export.")

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
