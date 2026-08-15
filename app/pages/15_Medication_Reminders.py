"""
15_Medication_Reminders.py
--------------------------
Medication reminder system for patients.
Generates reminders based on medication schedules and sends notifications.
"""

import streamlit as st
from datetime import date, datetime, timedelta

from app.core.security import SessionManager
from app.database.repositories.medication_repository import MedicationRepository
from app.database.repositories.message_repository import MessageRepository
from app.utils.custom_css import apply_theme, profile_widget, notification_bell, page_header

st.set_page_config(page_title="Medication Reminders", page_icon="⏰", layout="wide")
apply_theme()

user = SessionManager.get_current_user()
if not user:
    st.warning("Please log in first.")
    st.stop()

if user["role"] != "patient":
    st.error("Access denied.")
    st.stop()

profile_widget(user)
notification_bell(user)

st.markdown(page_header("⏰", "Medication Reminders", "Set up reminders to never miss your medications."), unsafe_allow_html=True)

med_repo = MedicationRepository()
msg_repo = MessageRepository()
patient_id = user["id"]

# Frequency to times per day mapping
FREQUENCY_TIMES = {
    "Once daily": 1,
    "Twice daily": 2,
    "Three times daily": 3,
    "Four times daily": 4,
    "Every morning": 1,
    "Every night": 1,
    "Every 8 hours": 3,
    "Every 12 hours": 2,
    "Weekly": 1,
    "As needed": 0,
}

active_meds = med_repo.list_for_patient(patient_id, active_only=True)

if not active_meds:
    st.info("No active medications. Add medications in the Medications page first.")
else:
    # ── Reminder Schedule ─────────────────────────────────────────
    st.markdown("### Your Reminder Schedule")

    reminder_times = {
        "Once daily": ["08:00 AM"],
        "Twice daily": ["08:00 AM", "08:00 PM"],
        "Three times daily": ["08:00 AM", "02:00 PM", "08:00 PM"],
        "Four times daily": ["08:00 AM", "12:00 PM", "04:00 PM", "08:00 PM"],
        "Every morning": ["08:00 AM"],
        "Every night": ["09:00 PM"],
        "Every 8 hours": ["08:00 AM", "04:00 PM", "12:00 AM"],
        "Every 12 hours": ["08:00 AM", "08:00 PM"],
        "Weekly": ["08:00 AM"],
        "As needed": [],
    }

    for med in active_meds:
        times = reminder_times.get(med.frequency, [])
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{med.name}** — {med.dosage}")
                st.caption(f"Frequency: {med.frequency}")
                if times:
                    st.caption(f"Reminder times: {', '.join(times)}")
                else:
                    st.caption("As needed — no scheduled reminders")
            with col2:
                if times:
                    st.success("✅ Active")

    # ── Send Reminder Messages ────────────────────────────────────
    st.markdown("---")
    st.markdown("### Send Reminder Now")

    st.info("Send a reminder message to yourself or ask your doctor to send reminders.")

    if st.button("📨 Send Daily Reminder Summary to My Doctor", width="stretch"):
        # Build reminder message
        med_list = "\n".join(
            f"  💊 {med.name} — {med.dosage} ({med.frequency})" for med in active_meds
        )
        times_info = []
        for med in active_meds:
            times = reminder_times.get(med.frequency, [])
            if times:
                times_info.append(f"  {med.name}: {', '.join(times)}")
        times_text = "\n".join(times_info) if times_info else "  No scheduled times"

        # Find doctor
        from app.database.repositories.patient_repository import PatientRepository
        patient_repo = PatientRepository()
        patient = patient_repo.get_by_user_id(patient_id)

        if patient and patient.assigned_doctor_id:
            msg_repo.send(
                sender_id=patient_id,
                receiver_id=patient.assigned_doctor_id,
                subject=f"⏰ Medication Reminder Request — {user['full_name']}",
                body=(
                    f"⏰ MEDICATION REMINDER REQUEST\n"
                    f"{'=' * 40}\n"
                    f"Patient: {user['full_name']}\n\n"
                    f"📋 ACTIVE MEDICATIONS:\n{med_list}\n\n"
                    f"🕐 SCHEDULED TIMES:\n{times_text}\n\n"
                    f"Please send me reminders at these times.\n"
                    f"{'=' * 40}"
                ),
            )
            st.success("✅ Reminder request sent to your doctor!")
        else:
            st.warning("No doctor assigned. Please contact support.")

    # ── Today's Checklist ─────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📋 Today's Medication Checklist")

    today_logs = med_repo.get_today_logs(patient_id)
    logged_ids = {log.medication_id for log in today_logs}

    for med in active_meds:
        already_logged = med.id in logged_ids
        log_for_today = next((l for l in today_logs if l.medication_id == med.id), None)

        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            if already_logged:
                status = "✅ Taken" if log_for_today.taken else "❌ Missed"
                st.markdown(f"**{med.name}** — {med.dosage} — {status}")
            else:
                st.markdown(f"**{med.name}** — {med.dosage} — ⏳ Pending")

        with col2:
            if not already_logged:
                if st.button("✅ Taken", key=f"rem_taken_{med.id}"):
                    med_repo.log_taken(med.id, patient_id, taken=True)
                    st.success(f"Logged: {med.name} taken")
                    st.rerun()

        with col3:
            if not already_logged:
                if st.button("❌ Missed", key=f"rem_missed_{med.id}"):
                    med_repo.log_taken(med.id, patient_id, taken=False)
                    st.warning(f"Logged: {med.name} missed")
                    st.rerun()

    # Today's summary
    if today_logs:
        taken_count = sum(1 for l in today_logs if l.taken)
        missed_count = sum(1 for l in today_logs if not l.taken)
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Total", len(active_meds))
        m2.metric("Taken ✅", taken_count)
        m3.metric("Missed ❌", missed_count)

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
