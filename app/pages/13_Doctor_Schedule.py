"""
13_Doctor_Schedule.py
---------------------
Doctor schedule management page.
Doctors can set their weekly availability for appointment booking.
"""

import streamlit as st
from datetime import time

from app.core.security import SessionManager
from app.database.repositories.doctor_schedule_repository import DoctorScheduleRepository, DAY_NAMES
from app.utils.custom_css import apply_theme, profile_widget, notification_bell

st.set_page_config(page_title="My Schedule", page_icon="📅", layout="wide")
apply_theme()

user = SessionManager.get_current_user()
if not user:
    st.warning("Please log in first.")
    st.stop()

if user["role"] != "doctor":
    st.error("Access denied.")
    st.stop()

profile_widget(user)
notification_bell(user)

st.title("📅 My Weekly Schedule")
st.caption("Set your availability for appointment booking.")

schedule_repo = DoctorScheduleRepository()
doctor_id = user["id"]

# Load existing schedule
existing = schedule_repo.get_schedule_for_doctor(doctor_id)
existing_map = {s.day_of_week: s for s in existing}

# ── Schedule Form ────────────────────────────────────────────────
st.markdown("### Set Your Weekly Availability")

with st.form("schedule_form"):
    st.info("Set your available hours for each day. Patients can only book appointments during your available hours.")

    schedule_data = {}
    for i, day in enumerate(DAY_NAMES):
        existing_day = existing_map.get(i)
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

        with col1:
            if i < 5:
                st.markdown(f"**{day}**")
            else:
                st.markdown(f"**{day}** 🏖️")

        with col2:
            default_start = existing_day.start_time if existing_day else time(9, 0)
            start = st.time_input(f"Start##{day}", value=default_start, key=f"start_{day}")

        with col3:
            default_end = existing_day.end_time if existing_day else time(17, 0)
            end = st.time_input(f"End##{day}", value=default_end, key=f"end_{day}")

        with col4:
            default_active = existing_day is not None
            active = st.checkbox("On", value=default_active, key=f"active_{day}")

        schedule_data[i] = {"start": start, "end": end, "active": active}

    if st.form_submit_button("💾 Save Schedule", use_container_width=True):
        saved_count = 0
        for day_idx, data in schedule_data.items():
            if data["active"]:
                if data["start"] >= data["end"]:
                    st.error(f"Invalid time for {DAY_NAMES[day_idx]}: start must be before end.")
                    continue
                schedule_repo.set_schedule(
                    doctor_id=doctor_id,
                    day_of_week=day_idx,
                    start_time=data["start"],
                    end_time=data["end"],
                    slot_duration_min=30,
                )
                saved_count += 1
            elif day_idx in existing_map:
                schedule_repo.delete_schedule(existing_map[day_idx].id)

        st.success(f"✅ Schedule saved! You are available on {saved_count} day(s).")
        st.rerun()

# ── Current Schedule Overview ────────────────────────────────────
st.markdown("---")
st.markdown("### Current Weekly Schedule")

if not existing:
    st.info("No schedule set yet. Use the form above to set your availability.")
else:
    for day_idx, day_name in enumerate(DAY_NAMES):
        schedule = existing_map.get(day_idx)
        if schedule:
            st.markdown(f"""
            <div style="background:#E7F4EF;border-left:4px solid #0E7A5C;border-radius:6px;
                 padding:10px 16px;margin:6px 0;">
                <strong>{day_name}</strong> — {schedule.start_time.strftime('%I:%M %p')} to {schedule.end_time.strftime('%I:%M %p')}
                <span style="color:#0E7A5C;margin-left:8px;">✓ Active</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#EFF3F1;border-left:4px solid #ccc;border-radius:6px;
                 padding:10px 16px;margin:6px 0;">
                <strong>{day_name}</strong> — <span style="color:#999;">Not available</span>
            </div>
            """, unsafe_allow_html=True)

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
